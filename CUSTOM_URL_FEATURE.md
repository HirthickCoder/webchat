# 🎯 Custom URL Scraping Feature

## What's New

You can now specify **exactly which pages** to scrape when creating a chatbot!

---

## How to Use

### Option 1: Automatic URLs (Default)
1. Enter Company Name
2. Enter Base Website URL
3. Click "Create"

**Automatically scrapes:**
- Base URL (e.g., https://example.com)
- /about page
- /services page
- /contact page
- /products page

---

### Option 2: Custom URLs (New!)
1. Enter Company Name
2. Enter Base Website URL
3. ✅ Check "🎯 Specify custom pages to scrape"
4. Enter specific URLs (one per line)
5. Click "Create"

**Example custom URLs:**
```
https://example.com/about
https://example.com/pricing
https://example.com/faq
https://example.com/testimonials
https://example.com/blog/getting-started
```

---

## Use Cases

### 1. **Specific Product Pages**
If you sell specific products, scrape those pages:
```
https://shop.com/product/phone
https://shop.com/product/laptop
https://shop.com/product/tablet
```

### 2. **Documentation Sites**
For SaaS or tech companies:
```
https://docs.example.com/getting-started
https://docs.example.com/api/overview
https://docs.example.com/pricing
https://docs.example.com/support
```

### 3. **Landing Pages**
For marketing campaigns:
```
https://example.com/landing/summer-sale
https://example.com/features
https://example.com/case-studies
```

### 4. **Multi-language Sites**
For international companies:
```
https://example.com/en/about
https://example.com/en/products
https://example.com/en/contact
```

### 5. **Deep Pages**
Access pages not in the main navigation:
```
https://example.com/company/team
https://example.com/resources/whitepaper
https://example.com/blog/latest-news
```

---

## Benefits

### ✅ Better Context
- Scrape exactly the information you need
- No irrelevant pages
- More focused chatbot responses

### ✅ Faster Creation
- Skip unnecessary pages
- Less time scraping
- Quicker initialization

### ✅ Better Answers
- Chatbot trained on relevant content
- More accurate responses
- Better user experience

---

## Tips

### 1. **Choose Relevant Pages**
- About Us
- Services/Products
- Pricing
- FAQ
- Contact

### 2. **Limit to 5-10 Pages**
- More pages = longer scraping time
- Focus on most important content
- Quality over quantity

### 3. **Use Full URLs**
Always include `https://`:
- ✅ `https://example.com/about`
- ❌ `example.com/about`
- ❌ `/about`

### 4. **Test URLs First**
Make sure URLs are accessible:
- Check in browser first
- Verify pages load correctly
- Ensure content is relevant

### 5. **Update as Needed**
- Can create new chatbot with different URLs
- Test which pages give best results
- Iterate and improve

---

## Examples

### Example 1: E-commerce Store
```
Company: ShopMart
Base URL: https://shopmart.com

Custom URLs:
https://shopmart.com/about-us
https://shopmart.com/products/electronics
https://shopmart.com/shipping-policy
https://shopmart.com/returns
https://shopmart.com/contact
```

### Example 2: SaaS Product
```
Company: CloudApp
Base URL: https://cloudapp.io

Custom URLs:
https://cloudapp.io/features
https://cloudapp.io/pricing
https://cloudapp.io/docs/getting-started
https://cloudapp.io/faq
https://cloudapp.io/security
```

### Example 3: Professional Services
```
Company: Legal Firm LLP
Base URL: https://legalfirm.com

Custom URLs:
https://legalfirm.com/about
https://legalfirm.com/practice-areas/corporate
https://legalfirm.com/practice-areas/litigation
https://legalfirm.com/attorneys
https://legalfirm.com/contact
```

### Example 4: Restaurant
```
Company: TastyBites
Base URL: https://tastybites.com

Custom URLs:
https://tastybites.com/menu
https://tastybites.com/locations
https://tastybites.com/catering
https://tastybites.com/reservations
https://tastybites.com/about
```

---

## Comparison

| Feature | Automatic URLs | Custom URLs |
|---------|---------------|-------------|
| Setup Time | ⚡ Fast (no input) | 🕐 Medium (enter URLs) |
| Control | ❌ Fixed pages | ✅ Full control |
| Flexibility | ❌ Limited | ✅ High |
| Best For | Standard sites | Specific needs |
| Pages Scraped | 5 fixed | Your choice |
| Accuracy | Good | Better |

---

## Troubleshooting

### Issue: "Failed to initialize chatbot"
**Solution:**
- Check URLs are correct and accessible
- Verify URLs start with `https://`
- Test each URL in browser first
- Ensure website allows scraping

### Issue: "No content extracted"
**Solution:**
- Some pages block scraping
- Try different pages
- Check page has visible text content
- Avoid pages with only images/videos

### Issue: "Slow creation"
**Solution:**
- Reduce number of URLs
- Choose pages with less content
- Check internet connection
- Some websites respond slowly

---

## Screenshot

When creating a chatbot, you'll see:

```
┌────────────────────────────────────┐
│ ➕ New Chatbot                    │
├────────────────────────────────────┤
│ Company Name                       │
│ [e.g., TechCorp          ]        │
│                                    │
│ Base Website URL                   │
│ [e.g., https://example.com]       │
│                                    │
│ ☐ 🎯 Specify custom pages to scrape│
│                                    │
│ [🚀 Create]                        │
└────────────────────────────────────┘
```

After checking the box:

```
┌────────────────────────────────────┐
│ ➕ New Chatbot                    │
├────────────────────────────────────┤
│ Company Name                       │
│ [TechCorp                ]        │
│                                    │
│ Base Website URL                   │
│ [https://techcorp.com    ]        │
│                                    │
│ ☑ 🎯 Specify custom pages to scrape│
│                                    │
│ Enter specific URLs (one per line):│
│ ┌──────────────────────────────┐  │
│ │https://techcorp.com/about    │  │
│ │https://techcorp.com/pricing  │  │
│ │https://techcorp.com/faq      │  │
│ └──────────────────────────────┘  │
│                                    │
│ [🚀 Create]                        │
└────────────────────────────────────┘
```

---

## Quick Start

### For Standard Websites:
1. Enter company name and URL
2. Click "Create" ✅
3. Done!

### For Custom Pages:
1. Enter company name and base URL
2. Check "Specify custom pages to scrape"
3. Add your URLs (one per line)
4. Click "Create" ✅
5. Done!

---

## Performance

### Automatic (5 pages):
- Scraping time: ~15 seconds
- Pages tried: 5
- Context quality: Good

### Custom (3 specific pages):
- Scraping time: ~9 seconds ⚡
- Pages used: 3
- Context quality: Better ✅

### Custom (10 pages):
- Scraping time: ~30 seconds
- Pages used: 10
- Context quality: Comprehensive

---

## Best Practices

### Do:
- ✅ Use HTTPS URLs
- ✅ Test URLs in browser first
- ✅ Choose 5-10 most relevant pages
- ✅ Include About, Contact, Services
- ✅ Update URLs as site changes

### Don't:
- ❌ Use too many URLs (>15)
- ❌ Include duplicate pages
- ❌ Use URLs that redirect
- ❌ Include login/protected pages
- ❌ Forget the protocol (https://)

---

## Summary

**New Feature:** Custom URL scraping gives you full control!

**Benefits:**
- 🎯 Choose exact pages
- ⚡ Faster creation (fewer pages)
- 📈 Better responses (relevant content)
- 🔧 Full flexibility

**Use When:**
- Need specific pages
- Standard pages don't exist
- Want better control
- Optimizing chatbot accuracy

**Stick with Auto When:**
- Standard website structure
- Quick setup needed
- /about, /services, /contact exist
- First time trying

---

**Test it now!** Create a new chatbot and try the custom URL feature! 🚀
