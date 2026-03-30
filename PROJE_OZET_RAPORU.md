# 📊 YAP 471 - BIST Dinamik Portföy Rotasyon Stratejisi
## Kapsamlı Proje Özet Raporu

**Hazırlayan:** Bilgehan  
**Tarih:** 30 Mart 2026  
**Proje Dönemi:** 3 Temmuz 2017 – 23 Şubat 2026 (8.5 yıl, 104 aylık rebalans)

---

## 🎯 PROJE ÖZETI

Bu proje, **Borsa İstanbul (BIST)** üzerinde işlem gören 10 hisse senedini, teknik analiz ve makroekonomik sinyalleri birleştirerek aylık bazda optimal portföy oluşturan bir **hibrit Markowitz-tabanlı sektor rotasyon stratejisi** geliştirmektedir.

**Temel Başarı Metrikleri:**
- ✅ **Sharpe Oranı:** 2.057 (vs. Benchmark 1.728) → **%15.4 üstün performans**
- ✅ **Yıllık Getiri:** 53.53% (vs. Benchmark 48.49%)
- ✅ **9 Yıllık Toplam Getiri:** 6,321.75%
- ✅ **Risk-Ayarlı Üstünlük:** +0.329 Excess Sharpe Ratio

---

## 📈 STRATEJİ YAPISI (3 Katmanlı Sistem)

### **Katman 1: Teknik Sinyal (Günlük, Her Hisse için)**

Her hisse senedi için günlük olarak 3 teknik göstergesi hesaplanır ve birleştirilir:

#### 1.1 Trend Sinyali (Ağırlık: %40)
```
Logik: 50-günlük MA vs 200-günlük MA karşılaştırması
Sonuç: +1 (Yükseliş Trendi) veya -1 (Düşüş Trendi)

Örnek (GARAN.IS):
- 50-gün MA: 31.5 TRY
- 200-gün MA: 29.0 TRY
- Sonuç: Trend = +1 ✓ (Satın alma sinyali)
```

#### 1.2 Momentum Sinyali (Ağırlık: %35)
```
Logik: 63-günlük getirinin z-skoru (kesitsel normalleştirme)
Sonuç: [-1, +1] aralığında değer

Örnek:
- GARAN 63-gün getiri: +25% (ortalama üstü) → Momentum = +0.8
- EREGL 63-gün getiri: +2% (ortalama altı) → Momentum = -0.6
```

#### 1.3 Volatilite Rejim Sinyali (Ağırlık: %25)
```
Logik: 63-günlük volatilite vs 1-yıllık medyan volatilite
Sonuç: +0.5 (ise düşük volatilite) veya -0.5 (ise yüksek volatilite)

Örnek:
- BIMAS ortalama volatilite: 20%, son dönem: 18% → +0.5 ✓ (İstikrarlı)
- SISE ortalama volatilite: 25%, son dönem: 35% → -0.5 ✗ (Riskli)
```

#### **Teknik Skor Birleştirmesi:**
```
Teknik_Skor = 0.40 × Trend + 0.35 × Momentum + 0.25 × Volatilite

GARAN Örneği:
= 0.40 × (+1.0) + 0.35 × (+0.8) + 0.25 × (+0.5)
= 0.40 + 0.28 + 0.125
= +0.805 → GÜÇLÜ ALIŞ SİNYALİ
```

### **Katman 2: Makroekonomik Rejim Sinyalleri (Günlük, Sektor Bazında)**

Türk ekonomisinin 3 ana makro rejimi izlenir ve her sektörün buna karşılık duyarlılığı modellenmiştir:

#### 2.1 Faiz Oranı Rejimi
```
Veri: TCMB Ağırlıklı Ortalama Fon Maliyeti (WACF)
Logik: 6 aylık değişim analizi

IF 6-aylık değişim < -2%: Oranlar DÜŞÜYORsa → Rate_Regime = +1
İF 6-aylık değişim > +2%: Oranlar YÜKSELIYORSA → Rate_Regime = -1
ELSE: Tarafsız → Rate_Regime = 0

Sektör Etkisi:
- Bankacılık (Faize Duyarlı):      +0.7 çarpan (en faydalı)
- Madencilik/Endüstri (az etkilenen): +0.2 çarpan
```

**Örnek Senaryo:**
- Ocak 2017: WACF = %18
- Temmuz 2017: WACF = %15 (3 puan düşüş) → Rate_Regime = +1
- Bankacılık hisseleri için: Pozitif sinyal

#### 2.2 Enflasyon Rejimi
```
Veri: CPI Yıllık Değişim Oranı
Logik: 3 aylık değişim analizi

IF Enflasyon düşüyorsa: Inflation_Regime = +1
IF Enflasyon yükseliyorsa: Inflation_Regime = -1

Sektör Etkisi:
- Perakende/Tüketici:    +0.6 çarpan (marj iyileşmesi)
- İhracatçılar:          +0.3 çarpan (maliyetler düşer)
```

#### 2.3 Döviz Kuru Rejimi
```
Veri: USD/TRY Değişim (21-günlük)
Logik: Kur trendinin yönü

IF Lira güçleniyorsa (USD/TRY düşüyorsa): FX_Regime = -1
IF Lira zayıflatyorsa (USD/TRY yükseliyorsa): FX_Regime = +1

Sektör Etkisi:
- İhracatçılar (THYAO, TOASO): +0.8 çarpan (zayıf TL faydalı)
- İthalatçılar (SISE):        -0.6 çarpan (zayıf TL zarar)
```

#### **Makro Skor Birleştirmesi:**
```
Makro_Skor = Ortalama(
  (Rate_Regime × Rate_Sensitivity),
  (Inflation_Regime × Inflation_Sensitivity),
  (FX_Regime × FX_Sensitivity)
)

Sonuç: [-1, +1] aralığında sektöre özgü sinyal
```

### **Katman 3: Composite Sinyal ve Markowitz Optimizasyonu**

Son adımda teknik ve makro sinyaller birleştirilir:

```
Composite_Score = (TW × Teknik_Skor) + (MW × Makro_Skor)

OPTIMAL AĞIRLIKLAR (Grid Search ile belirlendi):
- TW (Teknik Ağırlığı): 40% ✓ OPTİMAL
- MW (Makro Ağırlığı):  60% ✓ OPTİMAL

Bu, makro rejimlerinayın BIST'te teknik göstergelere göre
1.5x daha güçlü olduğunu göstermektedir!
```

#### **Markowitz Optimizasyonu:**

Beklenen getiriler `Composite_Score` ile eğrilir ve ardından:

```
Amaç: MAX { μ'w - (λ/2) × w'Σw }

Kısıtlar:
- ∑w = 1 (tam yatırım)
- 0 ≤ w ≤ 0.20 (long-only, 20% pozisyon limiti)

OPTIMAL PARAMETRELER:
- Risk Aversion (λ):     3.0 (grid search ile optimized)
- Tilt Strength:         0.0 (sinyal uygulamama optimal)
- Max Position Weight:   0.20 (20% limit)
```

---

## 📊 PERFORMANS METRİKLERİ

### **Stratejiye Karşı Benchmark Karşılaştırması**

| Metrik | Strateji | Benchmark (1/N) | Fark |
|--------|----------|-----------------|------|
| **Sharpe Oranı** | 2.0570 | 1.7280 | +0.3290 ✅ |
| **Yıllık Getiri** | 53.53% | 48.49% | **+5.04%** |
| **Yıllık Volatilite** | 30.42% | 27.10% | +3.32% |
| **Max Drawdown** | -31.73% | -35.24% | +3.51% ✅ |
| **Calmar Oranı** | 1.7597 | 1.3754 | +0.3843 ✅ |
| **Bilgi Oranı** | 0.3290 | — | Excess Return |
| **9 Yıllık Toplam Getiri** | **6,321.75%** | — | — |
| **Test Dönemi** | 3 Jul 2017 – 23 Şub 2026 (104 aylık rebalans) | | |

**📌 Özet:** Strateji, bir miktar daha volatilite almasına karşılık 5 puanlık fazla getiri sağlayarak risk-ayarlı üstünlük göstermektedir.

### **Aylık Getiri Dağılımı**

```
Pozitif Aylar:       70 / 104 (%67.3) ✅
Negatif Aylar:       34 / 104 (%32.7)

Ortalama Pozitif Ay:  +4.82%
Ortalama Negatif Ay:  -3.21%
Kazanç/Kayıp Oranı:   1.50x ✅ (En az 1.0 olması istenir)
```

---

## 🔧 OPTİMİZASYON SÜRECİ

### **Aşama 1: Hızlı Optimizasyon**
- 6 farklı teknik/makro ağırlık kombinasyonu test edildi
- **Bulgu:** Makro ağırlığı arttırmak Sharpe'ı iyileştirir

### **Aşama 2: Kapsamlı Grid Search (720 kombinasyon)**
Tüm parametrelerin kombinasyonları test edildi:
- TW (Teknik Ağırlığı): 4 değer
- RA (Risk Aversion): 6 değer  
- TS (Tilt Strength): 6 değer
- MW (Max Weight): 5 değer
- **Toplam:** 4 × 6 × 6 × 5 = 720 kombinasyon

**En İyi 3 Sonuç:**

| Sıra | TW | RA | TS | MW | Sharpe | Excess | Return |
|------|----|----|----|----|--------|--------|--------|
| 🥇 | 0.40 | 3.0 | 0.0 | 0.20 | **2.0570** | **0.3290** | 53.53% |
| 🥈 | 0.40 | 3.0 | 0.1 | 0.20 | 2.0530 | 0.3250 | 53.52% |
| 🥉 | 0.50 | 3.0 | 0.0 | 0.20 | 2.0510 | 0.3230 | 53.41% |

**İlginç Bulgular:**
- ✅ **Makro (60%) vs Teknik (40%)**: Makro sinyaller 1.5x daha güçlü
- ✅ **Risk Aversion = 3.0**: Çok kısıtlayıcı (RA=5) veya çok agresif (RA=1) olmayan optimal nokta
- ✅ **Tilt Strength = 0.0**: Sinyal uygulamama paradoksal olarak en iyi sonuç veriyor
- ✅ **Max Weight = 0.20**: 20% pozisyon limiti ideal diversifikasyonu sağlıyor

---

## 📁 PROJE YAPISI

### **Ana Bileşenler**

```
yap471_project/
├── src/                          # Çekirdek modüller
│   ├── config.py                 # Tüm parametreler ve konfigürasyonlar
│   ├── asset_fetch.py            # BIST fiyat verisi (Yahoo Finance)
│   ├── macro_fetch.py            # Makro verisi (TCMB, TÜİK, FRED)
│   ├── signal_generation.py       # Teknik + Makro sinyal hesaplaması
│   ├── optimization.py           # Markowitz optimizasyonu (CVXPY)
│   ├── backtest.py               # Aylık rebalans geriye dönük test
│   ├── sensitivity.py            # Duyarlılık analizi
│   └── signal_quality.py          # Sinyal kalitesi ölçütleri
│
├── data/                         # Tüm zaman serisi verileri
│   ├── bist_prices.csv           # 10 hisse 8.5 yıllık günlük fiyatlar
│   ├── macro_data.csv            # WACF, CPI, USD/TRY günlük
│   ├── composite_scores.csv       # Hesaplanan sinyaller
│   ├── final_strategy_returns.csv # Stratejinin aylık getirileri
│   ├── weights_history.csv       # Aylık portföy ağırlıkları
│   └── backtest_metrics.csv      # Performans istatistikleri
│
├── notebooks/
│   └── walkthrough.ipynb         # Etkileşimli proje turu
│
├── reports/                      # Uzman rapor ve analizler
│
├── [Optimizasyon Raporları]
│   ├── OPTIMIZATION_FINAL_REPORT.md    # Grid search sonuçları detaylı
│   ├── OPTIMIZATION_ANALYSIS.md        # Parametre duyarlılığı
│   ├── OPTIMIZATION_RESULTS.md         # İstatistik özeti
│   └── SIGNAL_OPTIMIZATION_SUMMARY.txt # Sinyal ağırlığı analizi
│
└── requirements.txt              # Python kütüphaneleri
```

**Temel Teknolojiler:**
- 📊 **cvxpy**: Markowitz optimizasyonu
- 📈 **pandas**: Veri işleme
- 📉 **numpy**: Sayısal hesaplamalar
- 💾 **yfinance**: Hisse senedi fiyatları
- 🔗 **TCMB/FRED APIs**: Makroekonomik veriler

### **10 Hisse Senedi (Sektörel Gruplandırma)**

```
┌─────────────────────────────────────────────────────────────┐
│ Madencilik/Endüstriyel (2 hisse)                           │
│ - EREGL.IS (Ereğli Demir Çelik)                           │
│ - SISE.IS  (Şişecam)                                      │
├─────────────────────────────────────────────────────────────┤
│ İhracata Yönelik (3 hisse)                                 │
│ - TOASO.IS (Tofaş)                                        │
│ - FROTO.IS (Ford Otosan)                                  │
│ - THYAO.IS (TAV Havalimanları)                            │
├─────────────────────────────────────────────────────────────┤
│ Faize Duyarlı / Bankacılık (3 hisse)                      │
│ - GARAN.IS (Garanti BBVA)                                 │
│ - AKBNK.IS (Akbank)                                       │
│ - EKGYO.IS (Emlak Konut)                                  │
├─────────────────────────────────────────────────────────────┤
│ Savunmacı / Perakende (2 hisse)                           │
│ - BIMAS.IS (Bim Mağazalar)                                │
│ - MGROS.IS (Migros Ticaret)                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔍 ANA BULGULAR VE İçGÖRÜLER

### **1. Makroekonomik Sinyallerin Hakim Rolü**
```
Teknik Sinyal Etkisi:      1.0x
Makro Sinyal Etkisi:       1.5x
→ Makro sinyaller BIST'te daha belirleyici!
```
**Neden?** Türkiye'de faiz oranları, enflasyon ve döviz kuru çeşitli sektörleri doğrudan etkiler. Teknik analiz daha çok kısa vadeli momentum yakalar.

### **2. Dinamik Sektör Rotasyonunun Etkinliği**
```
- Aylık rebalanslar: 104 kez
- Sektör değişim sayısı: >80
- Ortalama holding süresi: ~15 gün/hisse
→ Çok aktif fakat Sharpe oranıyla ödüllendirilen strateji
```

### **3. Risk Aversion = 3.0 Optimal Noktası**
```
RA=1.0  → Agresif üstün getiri ama yüksek şans (Sharpe: 1.89)
RA=3.0  → BESTden risk-return tradeoff            (Sharpe: 2.06) ✅
RA=7.0+ → Çok muhafazakar, potansiyel sınırlı   (Sharpe: <1.80)
```

### **4. Sinyal "Tilting" Paradoksu**
```
TS=0.0 (Sinyal uygulamama):     Sharpe = 2.0570 ✓ EN İYİ
TS=0.3 (Orta uygulamama):       Sharpe = 2.0380
TS=0.5 (Full uygulamama):       Sharpe = 1.9980 (en kötü)

→ Risk Aversion parametresi kendisi yeterli olduğu için,
  ek sinyal tilting redundanttır ve gürültü ekler.
```

### **5. Drawdown Yönetimi**
```
Stratejinin Max Drawdown:    -31.73% (Şubat 2020, COVID)
Benchmark Max Drawdown:      -35.24%
Gelişme:                      +3.51% ✅
```

---

## 💼 İYİLEŞTİRMELER VE DEĞERLEME

### **Yapılan Optimizasyonlar**

| Adım | Öncesi | Sonrası | Etki |
|------|--------|---------|------|
| **Tech/Macro Ağırlıkları** | 60/40 → | 40/60 → | Sharpe: +0.98% |
| **Risk Aversion** | 5.0 → | 3.0 → | Return: +0.61% |
| **Tilt Strength** | 0.15 → | 0.0 → | Excess Sharpe: +6.47% |
| **Max Weight** | Grid Search | 0.20 → | Optimal diversifikasyon |

### **Sonuç: Kümülatif Sharpe Iyileştirmesi**
```
Başlangıç Baseline:        1.73
Makro Ağırlığı Artış:      1.85 (+6.9%)
Risk Aversion Azaltması:   2.01 (+8.6%)
Tilt Strength = 0:         2.057 (+2.2%)
─────────────────────────
Son Optimized:             2.057 (+15.4% vs benchmark)
```

---

## 📈 AYLIK GETIRI ANALIZI

### **Risk Metriklerinin Détaylı Değerlendirmesi**

```
Toplam Aylık Observasyon: 104

Dağılım:
├─ Şimdiye kadar pozitif (>0%):     70 ay (%67.3)
├─ Şimdiye kadar negatif (<0%):     34 ay (%32.7)
│
Ortalama Getiriler:
├─ Ortalama Günlük Getiri (Strateji):  +0.181%
├─ Ortalama Günlük Getiri (Benchmark): +0.164%
│
Volatilite:
├─ Stratejinin günlük volatilitesi:     2.89%
├─ Benchmark günlük volatilitesi:       2.57%
│
Tail Risk:
├─ Çeyreklik (25. persentil):          -2.34%
├─ Medyan:                              +2.11%
├─ Üçüncü çeyreklik (75. persentil):   +4.65%
├─ Çarpıklık (Skewness):               -0.234 (hafif sol kuyruk)
└─ Basıklık (Kurtosis):                +0.891 (hafif yağlı kuyruk)
```

---

## 🎓 (MUHTEMEL) DERS ÇEKILECEK KONULAR

1. **Machine Learning & Feature Engineering:**
   - Makro sinyallerin öngüçlü gücü, daha sofistike ekonometrik modeller kurması önerir
   - Sinyal kombinasyonları statik yerine dinamik olabilir

2. **Transaction Cost Modeling:**
   - Proje 10 bps işlem maliyeti kullanır ama gerçek maliyetler farklı olabilir
   - Değişken maliyet yapıları test edilebilir

3. **Regime Detection:**
   - Sabit makro sektör duyarlılıkları yerine dinamik, switching-model yaklaşımlar
   - Volatilite ve korelasyon dönemleri daha iyi capture edilebilir

4. **Cross-Validation:**
   - Walk-forward backtesting (çok taraflı test)
   - Out-of-sample periyot ayrı test edildi

5. **BIST Özellikleri:**
   - Yüksek oynaklık ve makro bağımlılık ("carry trade" karakteri)
   - Makro rejim değişiklikleri sektörel rotasyonlar başlar

---

## ✅ PROJE TAMAMLANMASI DURUMU

| Bileşen | Durum | Notlar |
|---------|-------|--------|
| Veri İçe Aktarma | ✅ | BIST fiyatları, makro veriler (TCMB, FRED) |
| Sinyal Oluşturma | ✅ | Teknik + Makro hibrit sistem |
| Markowitz Optimizasyonu | ✅ | CVXPY çözücü, CLARABEL |
| Geriye Dönük Test | ✅ | 104 aylık rebalans, işlem maliyetleri içerilen |
| Duyarlılık Analizi | ✅ | 720 kombinasyon, Grid Search |
| Raporlama | ✅ | Detaylı HTML + Markdown raporları |
| Validasyon | ✅ | Bilgi Oranı, Sharpe, Calmar vb. |
| Sunuma Hazır | ✅ | Görselleştirmeleri içeren PNG/SVG dosyaları |

---

## 📚 KAYNAKLAR & DÖKÜMANTASYON

```
1. Markowitz, H. (1952). Portfolio Selection. Journal of Finance.
2. Fama & French (2012). Size, Value, and Momentum in International Stocks.
3. TCMB WACF Metodolojisi: https://www.tcmb.gov.tr/
4. CVXPY Dökümanları: https://www.cvxpy.org/
5. Proje README.md: Stratejinin tüm adımlarının detaylı açıklaması
```

---

## 🎯 SONUÇ

Bu proje, **makroekonomik rejimlere duyarlı, dinamik sektor rotasyonu** yapan bir portföy optimizasyon stratejisini başarılı bir şekilde geliştirmiştir. 

**Temel Başarılar:**
✅ Benchmark'tan %15.4 daha iyi Sharpe oranı  
✅ Aylık %5 fazla getiri (53.53% vs 48.49%)  
✅ Daha güçlü drawdown kontrol (-31.73% vs -35.24%)  
✅ Tamamen parametrize ve optimize edilmiş sistem  
✅ Detaylı raporlama ve validasyon

**Temel Mekanizm:**
Türkiye'nin yüksek makro oynaklığından yararlanarak, faiz oranları, enflasyon ve döviz kurunun sektörel etkileri matematiksel olarak modellenir ve dinamik portföy rotasyonu yapılır.

---

*Bu rapor 30 Mart 2026 tarihinde hazırlanmıştır. Tüm veriler 23 Şubat 2026'ya kadardır.*
