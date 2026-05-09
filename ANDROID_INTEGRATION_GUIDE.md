# ANDROID_INTEGRATION_GUIDE.md — Android Entegrasyon Rehberi

BasketScout Android uygulamasının bu backend servisi nasıl çağıracağını açıklar.

---

## Bağlantı Ayarları

```kotlin
// BasketScoutApiConfig.kt
object BasketScoutApiConfig {
    const val BASE_URL = "http://127.0.0.1:8787/"  // Yerel geliştirme
    // Üretimde: "https://your-server.example.com/"
    const val CONNECT_TIMEOUT = 10L  // saniye
    const val READ_TIMEOUT = 30L     // saniye (basket/compare için)
}
```

---

## Retrofit Tanımı (Örnek)

```kotlin
interface BasketScoutApi {
    @GET("health")
    suspend fun health(): HealthResponse

    @GET("products/search")
    suspend fun searchProducts(@Query("q") query: String): ProductSearchResponse

    @GET("prices/latest")
    suspend fun getPrices(
        @Query("product") product: String,
        @Query("postcode") postcode: String? = null
    ): PricesResponse

    @POST("basket/compare")
    suspend fun compareBasket(@Body request: BasketCompareRequest): BasketCompareResponse

    @GET("providers/status")
    suspend fun getProviderStatus(): ProvidersStatusResponse
}
```

---

## Veri Modelleri (Örnek)

```kotlin
data class PriceItem(
    val retailer: String,
    val retailerSlug: String,
    val product: String,
    val price: Double,
    val currency: String,
    val loyaltyPrice: Double?,
    val ownBrand: Boolean,
    val available: Boolean?,
    val source: String,
    val lastCheckedAt: String,
    val confidence: Double,
    val isStale: Boolean
)

data class BasketCompareRequest(
    val postcode: String?,
    val coverageThreshold: Double = 0.9,
    val useLoyaltyPrices: Boolean = false,
    val allowOwnBrand: Boolean = true,
    val items: List<BasketItem>
)
```

---

## Güven Skoru Kullanımı

Android uygulaması `confidence` ve `is_stale` değerlerini kullanarak
kullanıcıya uyarı göstermeli:

```kotlin
fun getPriceStatusText(item: PriceItem): String {
    return when {
        item.source == "mock" -> "Demo veri"
        item.isStale -> "Güncel olmayabilir"
        item.confidence >= 0.9 -> "Güncel"
        item.confidence >= 0.6 -> "Yaklaşık fiyat"
        else -> "Tahmini fiyat"
    }
}
```

---

## Çevrimdışı Davranış

Backend erişilemez olduğunda:

```kotlin
// BackendPriceProvider.kt (plan)
class BackendPriceProvider(private val api: BasketScoutApi) : PriceProvider {
    override suspend fun getPrices(query: String, postcode: String?): List<PriceResult> {
        return try {
            val response = api.getPrices(query, postcode)
            response.items.map { it.toDomain() }
        } catch (e: IOException) {
            // Backend erişilemiyor — boş liste döndür, kullanıcıya bildir
            emptyList()
        }
    }
}
```

---

## Sepet Karşılaştırma Entegrasyonu

```kotlin
suspend fun comparePrices(
    items: List<ShoppingItem>,
    postcode: String?
): BasketCompareResult {
    val request = BasketCompareRequest(
        postcode = postcode,
        coverageThreshold = 0.9,
        useLoyaltyPrices = userPreferences.useLoyaltyCards,
        allowOwnBrand = userPreferences.allowOwnBrand,
        items = items.map { BasketItem(name = it.name, quantity = it.quantity) }
    )
    return api.compareBasket(request)
}
```

---

## Önemli Notlar

1. `data_mode: "mock"` → Gerçek fiyat değil, UI'da belirt.
2. `is_stale: true` → TTL aşıldı, uyarı göster.
3. `available: null` → Stok bilgisi yok, "Bilinmiyor" göster.
4. Backend bağlantısı yoksa app çalışmaya devam etmeli.
5. Timeout: `/basket/compare` en fazla 30 saniye sürebilir.

---

## Geliştirme Testi

Android emülatöründen yerel backend'e bağlanmak için:

```
http://10.0.2.2:8787/  ← Android emülatörü için localhost
http://127.0.0.1:8787/ ← Fiziksel cihaz (aynı ağda)
```
