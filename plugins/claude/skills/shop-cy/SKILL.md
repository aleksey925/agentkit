---
name: shop-cy
description: Context about online stores in Cyprus — what's available, how to access each store, product categories. Useful for product search, price comparison, stock availability, or marketplace research on the Cyprus market.
---

# Cyprus Online Stores

Known electronics and home appliance stores operating in Cyprus. This is **not an exhaustive list** — other stores exist. When searching for products, consider that additional stores may be found via web search.

## Before you start

**Every store here needs a real browser — use the `/browse` skill.** It owns the
browsing tooling, its setup, and its quirks (redirects, bot checks); this skill
does not repeat any of that. Get the browser working **before** starting any
searches, not mid-way through.

**Do NOT use WebFetch for store product pages.** E-commerce listings, search
results, and category pages load via AJAX/JS, so WebFetch returns empty or
partial results — including on stores whose homepage renders fine.

WebFetch is still the faster choice for:
- **sitemap XML** — for category discovery when adding a store
- static info pages (about, contact, delivery, terms)

## Store Directory

| Store | URL | Focus |
|---|---|---|
| Singular | https://www.singular.com.cy/ | Broad IT/electronics: PCs, components, POS systems, networking, gaming, office & business |
| MS Electronics | https://www.mstronics.com/ | Comprehensive IT/B2B + consumer: networking, security, ProSound & lighting, power/solar, smart home (KNX), home & health, Digital TV/SAT |
| Needy Shop | https://needy.shop/ | Custom/gaming PCs, laptops, PC components & networking, sound & vision, gaming, printing, home & health, mobile, furniture |
| Laptops Clearance | https://laptopsclearance.com.cy/ | Refurbished/clearance laptops, desktops, monitors, peripherals. **Unstable** — site was down as of 2026-03-21 |
| Jinius | https://www.jinius.com.cy/en/home/ | General marketplace: tech, fashion, beauty, toys & games, home & garden, books, baby, pets, DIY, health, gifts |
| Stephanis | https://www.stephanis.com.cy/en | Broad: IT, sound & vision, telecom, gaming, appliances, seasonal (Christmas/Halloween/carnival/pools/beach), pets, collectibles |
| Bionic | https://bionic.com.cy/ | PC components, networking, gaming/esports, B2B IT, also EV chargers, Nespresso, power stations |
| Techmart | https://techmart.com.cy/ | Consumer electronics, appliances, built-in, AC/heating, auto accessories, house & garden |
| Lazanias | https://lazanias.com/ | Premium appliances (Gaggenau, Miele, Bosch, Neff, Siemens), built-in, kitchenware, sound & vision |
| Electroline | https://electroline.cy/en/ | Major chain: full electronics, appliances, garden/tools, toys, stationery, fitness, smart home, CYTA telecom |
| PrestigioPlaza | https://prestigioplaza.com/ | Premium boutique (B&O, Devialet, Sonos, Loewe), simracing, wine accessories, smart home |
| Kotsovolos | https://www.kotsovolos.cy/ | Major chain: appliances, electronics, AC/heating, personal care, fitness, garden/tools, cameras, services, telecom contracts (Greek site) |
| Public | https://www.public.cy/ | Tech, books, music (vinyl/CDs), toys, gaming, school supplies, pet shop, furniture & decor (Greek chain) |
| Rolls | https://rolls.cy/ | AC/heating, white goods, kitchen & coffee, professional catering equipment, sound & vision, computing, personal care, PV systems, heat pumps |
| Garmin Cyprus | https://www.garmincyprus.com/ | Authorised Garmin distributor: smartwatches, fitness/running/cycling/golf, outdoor handhelds, marine electronics, automotive GPS, dash cams, dog tracking, Tacx trainers, Shokz, JL Audio |
| iStorm | https://istorm.com.cy/ | Apple Premium Partner: iPhone, iPad, Mac, Apple Watch, AirPods, Apple TV, Studio Display; also Beats, Sonos, JBL, Marshall, B&W, Belkin, Philips Hue, Aqara, Satechi, LaCie, Thule |
| Gomibo | https://www.gomibo.cy/en/ | Phone specialist (600+ models, 25+ brands, incl. refurbished & rugged), tablets, and phone/audio/wearable accessories. Online-only, ships from own stock. No appliances, no PC components |

## Detailed Product Categories

See [`stores-directory.md`](stores-directory.md) for a full breakdown of product categories available at each store. Use it to decide which stores to search for a given product type.

## Notes

- All stores operate in EUR
- Many stores have both English and Greek versions; prefer English (`/en/`) where available
- Delivery is typically Cyprus-wide; some stores offer free delivery above a threshold
- For price comparison, also consider checking international stores that ship to Cyprus

## Maintaining This Skill

When adding a new store:

1. **Research categories** — browse the store and document all product
   categories it carries. The sitemap is the fastest map of the catalogue: read
   `robots.txt` first for its `Sitemap:` line, since it is often not at
   `/sitemap.xml` and may split into per-section sitemaps.
2. **Update `SKILL.md`** — add the store to the table with URL and short focus
   summary.
3. **Update `stores-directory.md`** — add a detailed category listing, plus a
   `**Notes:**` line for any per-store quirk worth knowing next time.
4. **Verify accuracy** — don't guess categories. Only document what you've
   confirmed by visiting the site.
5. **Include non-core categories** — stores often carry products outside their
   main specialization (e.g., a construction store may sell routers, a premium
   appliance store may stock TVs). Document ALL categories found on the site,
   not just the ones matching the store's primary focus. The "Focus" column in
   the table should reflect the store's main identity, but
   `stores-directory.md` must list everything they actually sell.
6. **Flag empty categories** — a category page can exist and render filters
   while carrying zero products. Note those, so a later search doesn't retry them.
