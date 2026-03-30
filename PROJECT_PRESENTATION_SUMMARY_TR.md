# 1. Giriş ve Problem
- **Projenin konusu:** BIST’te 10 hisselik bir evrende, teknik + makro sinyalleri birleştirip aylık yeniden dengelemeli (monthly rebalance) **Markowitz tabanlı dinamik portföy rotasyonu** yapmak.
- **Çözülmek istenen finansal problem:** Statik eşit ağırlıklı portföyün rejim değişimlerinde (faiz, enflasyon, kur şokları) zayıf kalması; risk-ayarlı getiriyi artıracak sistematik bir tahsis mekanizması kurmak.
- **Neden seçildiği (uygulamadan okunan gerekçe):**
  - Türkiye piyasasında makro rejim etkileri kuvvetli (WACF, CPI, USD/TRY doğrudan modele giriyor).
  - Sektörel farklılaşma belirgin olduğu için rotasyon yaklaşımı anlamlı.
- **Temel amaç:** Uzun-only, kısıtlı Markowitz optimizasyonu ile benchmark’a göre daha yüksek Sharpe ve daha dengeli drawdown profili elde etmek.
- **Varlık evreni / sektör mantığı (kodda sabit):**
  - Mining/Industrial: `EREGL.IS`, `SISE.IS`
  - Export-Oriented: `TOASO.IS`, `FROTO.IS`, `THYAO.IS`
  - Interest-Sensitive: `GARAN.IS`, `AKBNK.IS`, `EKGYO.IS`
  - Defensive/Retail: `BIMAS.IS`, `MGROS.IS`
- **Türkiye/BIST odağı:** Veri kaynakları ve sinyaller Türkiye’ye özgü kurulmuş (EVDS’den WACF ve CPI, USD/TRY; BIST hisseleri).
- **Proposal-kod farkı (kısa):**
  - Proposal’da ETF/altın sertifikası opsiyonu var, implementasyonda yok.
  - Proposal “3 yıl taban” derken implementasyon ~2016-2026 veri penceresinde.
  - Proposal’daki “team roles” kod akışında zaten operasyonel bir unsur değil.

# 2. Sinyal Sistemi
- **Genel mantık:** Günlük bazda her hisse için teknik skor + sektör bazlı makro skor üretiliyor; sonra birleşik skor portföy optimizasyonuna giriyor.
- **Teknik göstergeler:**
  - Trend: `MA50 > MA200` ise +1, değilse -1
  - Momentum: 63 günlük getirinin kesitsel z-skoru, `[-1,1]`e kırpılıyor
  - Volatilite rejimi: 63g volatilite, 252g medyana göre düşükse +0.5, yüksekse -0.5
  - Teknik skor: `0.40*trend + 0.35*momentum + 0.25*vol`
- **Makro göstergeler:**
  - Faiz rejimi: WACF’in ~6 aylık değişimi (126 işlem günü)
  - Enflasyon rejimi: CPI YoY’nin ~3 aylık değişimi (63 işlem günü)
  - Kur rejimi: USD/TRY 1 aylık değişimi (`USDTRY_CHG_1M`)
- **Rejim/skor/karar yapısı:**
  - Her makro rejim sinyali sektör duyarlılık katsayılarıyla çarpılıyor.
  - Sektör duyarlılık matrisi kodda sabit (ör. Interest-Sensitive için faiz etkisi yüksek).
  - Birleşik skor: `tech_weight * teknik + macro_weight * makro` (default config: 0.40 / 0.60).
- **Veri eşleştirme ve hazırlık:**
  - Fiyatlar: `yfinance`, `auto_adjust=True`; `ffill`, tümü NaN satırlar atılır.
  - Sentetik işlem günü temizliği: tüm hisselerde fiyatın önceki günle birebir aynı olduğu satırlar çıkarılıyor.
  - Makro panel: işlem takvimine hizalanıyor; yayın gecikmesi uygulanıyor (`USDTRY/WACF +1 gün`, `CPI +1 ay`), metadata’da da kayıtlı.
- **Sinyalin portföy kararına etkisi:**
  - Aylık rebalance tarihinde en güncel skor satırı alınarak optimizasyona giriyor.
  - Ek olarak bazı akışlarda “signal confidence” ile skorlar ağırlıklanıyor (`scores * confidence`).

# 3. Markowitz Modeli
- **Projede kullanım:** Mean-variance optimizasyonu, aylık periyotta yeniden çözülüyor.
- **Beklenen getiri vektörü (`mu`):**
  - Temel kurulum: son `lookback` (default 252 gün) günlük getirilerin ortalaması yıllıklandırılıyor (`*252`).
- **Kovaryans matrisi (`Sigma`):**
  - Son 252 gün kovaryans, yıllıklandırma (`*252`).
  - Diagonal shrinkage: `S_shrunk = (1-a)S + a*diag(S)`, default `a=0.30`.
  - Skor bazlı risk ölçekleme ile düşük skorlu varlıklara daha yüksek risk çarpanı uygulanıyor.
- **Amaç fonksiyonu:**
  - `max  mu'w - (gamma/2) * w' Sigma w`
  - Çözücü: `cvxpy` + `CLARABEL`.
- **Kısıtlar:**
  - `sum(w)=1`
  - `0 <= w <= max_weight`
  - no-short (long-only)
- **Rebalancing:**
  - Her ayın son işlem günü ağırlık hesaplanıyor, bir sonraki rebalance tarihine kadar tutuluyor.
  - `final_weights_history.csv` 2017-06-30’dan 2026-01-30’a kadar **104** aylık ağırlık içeriyor.
- **Benchmark ilişkisi:**
  - Ana benchmark: aynı 10 hissede `1/N` eşit ağırlık.
  - XU100 karşılaştırması ayrı bir ileri analiz modülünde var; ana backtest benchmark’ı değil.

# 4. Performans ve Sonuç
- **Backtest tasarımı (uygulama):**
  - Günlük getirilerden, aylık rebalance döngüsü ile simülasyon.
  - Çıktı serileri: strateji ve benchmark günlük getirileri.
  - `final_strategy_returns.csv` ve `final_benchmark_returns.csv` dönemi: **2017-07-03 -> 2026-02-23** (2166 işlem günü).
- **Kullanılan metrikler:**
  - Total Return, Annual Return, Annual Volatility, Sharpe, Max Drawdown, Calmar.
- **Dosya-bazlı sayısal bulgular (önemli):**
  - `data/backtest_metrics.csv` (temel backtest çalıştırması):
    - Strategy: **Sharpe 1.923**, Yıllık Getiri **%60.64**, Vol **%31.54**, MaxDD **-%35.25**
    - Benchmark: **Sharpe 1.728**, Yıllık Getiri **%48.49**, Vol **%28.07**
  - `data/FINAL_CONFIGURATION_SUMMARY.csv` (confidence-weighted + işlem maliyeti 10 bps):
    - Strategy Sharpe **2.031**, Benchmark Sharpe **1.728**, Excess **0.303**
    - Strategy yıllık getiri **%61.41**, vol **%30.23**, MaxDD **-%31.22**
    - Toplam turnover **%1248.68**, toplam maliyet **124.87 bps**
  - `data/optimization_summary.csv` ve `data/comprehensive_optimization_full.csv`:
    - 720 kombinasyon taramasında en iyi konfigürasyon:
    - **TW=0.40, MWacro=0.60, RA=3.0, MaxW=0.20**
    - Sharpe **2.057**, Excess **0.329**
- **Sonuçların yorumu:**
  - Strateji genel olarak benchmark’ı risk-ayarlı ölçekte geçiyor.
  - Ancak farklı script/deney setleri farklı “en iyi” parametreler raporluyor; bu nedenle sonuçları tek bir nihai tabloya bağlarken deney koşullarını belirtmek gerekli.
- **Güçlü yönler:**
  - Veri gecikmesi (lag) ve takvim hizalaması bilinçli uygulanmış.
  - Kısıtlı, uzun-only ve cap’li optimizasyon pratikte uygulanabilir.
  - Sinyal + optimizasyon + backtest + duyarlılık analizleri uçtan uca mevcut.
- **Zayıf yönler / limitasyonlar:**
  - Sonuç raporlarında tutarsızlıklar var (farklı dosyalarda farklı “optimal” setler).
  - Parametre optimizasyonu büyük ölçüde aynı tarih aralığında yapıldığı için overfitting riski var.
  - Sharpe hesaplarında risksiz faiz açıkça modellenmemiş.
  - İşlem maliyeti/sürüklenme modellemesi sade; tüm deneylerde tutarlı uygulanmıyor.
  - Dokümanlarda “haftalık rebalance” gibi kodla çelişen ifadeler var; kod gerçekte aylık.
- **Geliştirme alanları:**
  - Walk-forward / out-of-sample validasyon.
  - Rejim bazlı dinamik risk aversion.
  - Daha gerçekçi maliyet modeli (spread, kayma, likidite).
  - Tek bir “resmi” deney protokolü ve sürüm bazlı sonuç dosyası standardı.
- **Genel çıkarım:**
  - Proje, BIST için uygulanabilir bir hibrit sinyal + Markowitz iskeleti kurmuş.
  - Sunumda en doğru yaklaşım: “metodoloji güçlü, sonuçlar benchmark üstünde; fakat nihai parametre seti için deney standardizasyonu gerekli.”

# 5. Sunum İçin Kısa Akış Önerisi
1. Problem ve motivasyon: BIST’te rejim değişimleri ve statik portföy sınırı
2. Veri ve varlık evreni: 10 hisse, 4 sektör, Yahoo + EVDS, lag-safe hizalama
3. Sinyal sistemi: teknik + makro rejim + sektör duyarlılık matrisi
4. Markowitz optimizasyonu: amaç fonksiyonu, kısıtlar, aylık rebalance
5. Backtest ve performans: benchmark karşılaştırması, temel metrikler
6. Duyarlılık analizleri: RA/MaxWeight etkisi
7. Güçlü yönler, limitasyonlar ve net geliştirme planı
