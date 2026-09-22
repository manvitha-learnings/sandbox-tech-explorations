import logging
from typing import List, Optional
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from pydantic import BaseModel, Field

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ProductMcpServer")

mcp = FastMCP(
    "ProductResearchServer",
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=False,
    )
)

# Product Data Model
# Product Data Model
class Product(BaseModel):
    id: str = Field(..., description="Unique product ID")
    name: str = Field(..., description="Product name")
    brand: str = Field(..., description="Brand of the product")
    price: float = Field(..., description="Price in USD")
    url: str = Field(..., description="Link to the official product page or store")
    specs: dict = Field(..., description="Technical specifications")
    description: str = Field(..., description="Short marketing description")
    pros: List[str] = Field(default_factory=list, description="Pros for programming/use")
    cons: List[str] = Field(default_factory=list, description="Cons for programming/use")

# In-memory mock product database
PRODUCTS_DB = [
    # --- LAPTOPS ---
    Product(
        id="lenovo-thinkpad-e14",
        name="ThinkPad E14 Gen 5 AMD",
        brand="Lenovo",
        price=749.00,
        url="https://www.lenovo.com/us/en/p/laptops/thinkpad/thinkpade/thinkpad-e14-gen-5-(14-inch-amd)/len101t0067",
        specs={
            "Category": "Laptop",
            "CPU": "AMD Ryzen 5 7530U (6 Cores, 12 Threads)",
            "RAM": "16GB DDR4",
            "Storage": "512GB NVMe SSD",
            "Display": "14-inch IPS FHD+ (1920x1200), Anti-glare",
            "Battery": "57Wh (up to 10 hours)",
            "OS": "Windows 11 Home",
            "Weight": "3.37 lbs"
        },
        description="Reliable business laptop with an industry-leading keyboard, solid durability, and great performance-to-price ratio for development.",
        pros=["Industry-leading keyboard comfort", "Excellent durability", "Upgrade-friendly RAM/SSD slot", "Quiet operation"],
        cons=["Display brightness is average (300 nits)", "Build is partially plastic"]
    ),
    Product(
        id="acer-swift-go-14",
        name="Swift Go 14 OLED",
        brand="Acer",
        price=699.00,
        url="https://www.acer.com/us-en/laptops/swift/swift-go",
        specs={
            "Category": "Laptop",
            "CPU": "Intel Core i5-13500H (12 Cores, 16 Threads)",
            "RAM": "16GB LPDDR5",
            "Storage": "512GB NVMe SSD",
            "Display": "14-inch OLED 2.8K (2880x1800), 90Hz",
            "Battery": "65Wh (up to 8 hours)",
            "OS": "Windows 11 Home",
            "Weight": "2.76 lbs"
        },
        description="Thin, lightweight laptop featuring a stunning 2.8K OLED display and a high-performance H-series Intel CPU, perfect for multitasking.",
        pros=["Gorgeous 2.8K OLED screen", "High-performance H-series CPU", "Extremely lightweight and portable"],
        cons=["Slightly shorter battery life due to high-performance CPU", "RAM is soldered and not upgradable"]
    ),
    Product(
        id="apple-macbook-air-m2",
        name="MacBook Air 13.6-inch M2",
        brand="Apple",
        price=899.00,
        url="https://www.apple.com/macbook-air/",
        specs={
            "Category": "Laptop",
            "CPU": "Apple M2 (8-core CPU, 8-core GPU)",
            "RAM": "8GB Unified Memory",
            "Storage": "256GB SSD",
            "Display": "13.6-inch Liquid Retina (2560x1664)",
            "Battery": "52.6Wh (up to 18 hours)",
            "OS": "macOS",
            "Weight": "2.7 lbs"
        },
        description="Sleek, fanless ultraportable powered by Apple M2 silicon. Outstanding battery life and Unix-based OS environment ideal for coding.",
        pros=["Phenomenal battery life (18 hours)", "Fanless, silent operation", "Excellent trackpad and macOS ecosystem"],
        cons=["Only 8GB RAM and 256GB storage at this price (non-upgradable)", "Limited external monitor support (only 1)"]
    ),
    Product(
        id="hp-pavilion-plus-14",
        name="Pavilion Plus 14 AMD",
        brand="HP",
        price=849.00,
        url="https://www.hp.com/us-en/shop/pdp/hp-pavilion-plus-laptop-14z-ey000-14-802m2av-1",
        specs={
            "Category": "Laptop",
            "CPU": "AMD Ryzen 7 7840U (8 Cores, 16 Threads) with Radeon 780M",
            "RAM": "16GB LPDDR5X",
            "Storage": "1TB NVMe SSD",
            "Display": "14-inch OLED 2.8K (2880x1800), 120Hz",
            "Battery": "68Wh (up to 9 hours)",
            "OS": "Windows 11 Home",
            "Weight": "3.08 lbs"
        },
        description="Premium mid-range laptop sporting a fast Ryzen 7 Zen 4 processor, massive 1TB SSD, and a fluid 120Hz OLED screen.",
        pros=["Super-fast Ryzen 7 7840U processor", "Generous 1TB SSD storage", "Smooth 120Hz refresh rate OLED screen"],
        cons=["RAM is soldered", "Webcam privacy switch is manual/flimsy"]
    ),
    Product(
        id="asus-zenbook-14",
        name="Zenbook 14 OLED",
        brand="ASUS",
        price=799.00,
        url="https://www.asus.com/us/laptops/for-home/zenbook/zenbook-14-oled-ux3405/",
        specs={
            "Category": "Laptop",
            "CPU": "AMD Ryzen 7 7730U (8 Cores, 16 Threads)",
            "RAM": "16GB LPDDR4X",
            "Storage": "512GB NVMe SSD",
            "Display": "14-inch OLED 2.8K (2880x1800), 90Hz",
            "Battery": "75Wh (up to 11 hours)",
            "OS": "Windows 11 Home",
            "Weight": "3.06 lbs"
        },
        description="Elegant premium laptop with a massive 75Wh battery, superb battery efficiency, and a beautiful OLED display.",
        pros=["Outstanding battery life for an OLED laptop", "Sophisticated premium design and chassis", "Ergofit hinge design makes typing comfortable"],
        cons=["Ryzen 7 7730U is a rebranded older-gen Zen 3 chip", "RAM is soldered"]
    ),
    Product(
        id="dell-inspiron-14-plus",
        name="Inspiron 14 Plus",
        brand="Dell",
        price=999.00,
        url="https://www.dell.com/en-us/shop/dell-laptops/inspiron-14-plus-laptop/spd/inspiron-14-7440-laptop",
        specs={
            "Category": "Laptop",
            "CPU": "Intel Core i7-13620H (10 Cores, 16 Threads)",
            "RAM": "16GB LPDDR5",
            "Storage": "1TB NVMe SSD",
            "Display": "14-inch 2.5K (2560x1600) ComfortView Plus",
            "Battery": "64Wh (up to 8.5 hours)",
            "OS": "Windows 11 Home",
            "Weight": "3.5 lbs"
        },
        description="Performance-focused Dell laptop with 13th gen H-series Core i7, offering desktop-class computing in a portable form factor.",
        pros=["Powerful i7-13620H processor", "Crisp 2.5K 16:10 aspect ratio screen", "1TB fast storage"],
        cons=["Slightly heavier (3.5 lbs) than competitors", "Fans can get loud under load"]
    ),
    Product(
        id="apple-macbook-pro-14",
        name="MacBook Pro 14 M3",
        brand="Apple",
        price=1599.00,
        url="https://www.apple.com/macbook-pro/",
        specs={
            "Category": "Laptop",
            "CPU": "Apple M3 (8-core CPU, 10-core GPU)",
            "RAM": "16GB Unified Memory",
            "Storage": "512GB SSD",
            "Display": "14.2-inch Liquid Retina XDR (3024x1964), 120Hz ProMotion",
            "Battery": "70Wh (up to 22 hours)",
            "OS": "macOS",
            "Weight": "3.4 lbs"
        },
        description="The gold standard for mobile developers. Stunning screen, phenomenal efficiency, and massive developer community support.",
        pros=["Unmatched performance and efficiency M3 chip", "Liquid Retina XDR screen is best-in-class", "Stellar 22-hour battery life"],
        cons=["Well over the $1,000 budget limit", "No user upgradeable parts"]
    ),
    Product(
        id="dell-xps-15",
        name="XPS 15 9530",
        brand="Dell",
        price=1899.00,
        url="https://www.dell.com/en-us/shop/dell-laptops/xps-15-laptop/spd/xps-15-9530-laptop",
        specs={
            "Category": "Laptop",
            "CPU": "Intel Core i9-13900H (14 Cores, 20 Threads)",
            "RAM": "32GB DDR5",
            "Storage": "1TB NVMe SSD",
            "Display": "15.6-inch OLED 3.5K (3456x2160) Touchscreen",
            "Battery": "86Wh (up to 7 hours)",
            "OS": "Windows 11 Pro",
            "Weight": "4.23 lbs"
        },
        description="Ultra-premium workstation with massive computing power, dedicated NVIDIA GeForce RTX 4060 graphics, and sleek carbon-fiber palm rest.",
        pros=["High-end i9 processor and 32GB RAM", "Beautiful infinity-edge display", "Dedicated GPU for ML/gaming"],
        cons=["Extremely expensive (well above budget)", "Poor battery life due to high-power components", "Heavy (4.2 lbs)"]
    ),
    Product(
        id="lenovo-thinkpad-t14s",
        name="ThinkPad T14s Gen 4 AMD",
        brand="Lenovo",
        price=1299.00,
        url="https://www.lenovo.com/us/en/p/laptops/thinkpad/thinkpadt/thinkpad-t14s-gen-4-(14-inch-amd)/len101t0058",
        specs={
            "Category": "Laptop",
            "CPU": "AMD Ryzen 7 PRO 7840U (8 Cores, 16 Threads)",
            "RAM": "32GB LPDDR5X",
            "Storage": "1TB NVMe SSD",
            "Display": "14-inch IPS Low Power FHD+ (400 nits)",
            "Battery": "57Wh (up to 12 hours)",
            "OS": "Windows 11 Pro",
            "Weight": "2.77 lbs"
        },
        description="The developers' favorite. Outstanding keyboard, lightweight carbon/magnesium chassis, exceptional 32GB RAM, and a highly efficient CPU.",
        pros=["Ideal specs: Ryzen 7 Zen 4 + 32GB RAM", "Extremely light and durable", "Excellent Linux compatibility"],
        cons=["Price is slightly above the $1,000 threshold"]
    ),
    # --- TABLETS ---
    Product(
        id="apple-ipad-air-m2",
        name="iPad Air 11-inch M2",
        brand="Apple",
        price=599.00,
        url="https://www.apple.com/ipad-air/",
        specs={
            "Category": "Tablet",
            "CPU": "Apple M2 (8-core CPU, 9-core GPU)",
            "RAM": "8GB Unified Memory",
            "Storage": "128GB SSD",
            "Display": "11-inch Liquid Retina IPS (2360x1640)",
            "Battery": "28.93Wh (up to 10 hours)",
            "OS": "iPadOS",
            "Weight": "1.02 lbs"
        },
        description="Highly portable productivity tablet powered by Apple M2 silicon. Outstanding performance and compatibility with Apple Pencil Pro.",
        pros=["Powerful Apple M2 chip", "Lightweight, premium aluminum design", "Supports Pencil Pro and Magic Keyboard"],
        cons=["iPadOS has multitasking constraints", "Base storage is 128GB (non-upgradeable)"]
    ),
    Product(
        id="apple-ipad-pro-m4",
        name="iPad Pro 11-inch M4",
        brand="Apple",
        price=999.00,
        url="https://www.apple.com/ipad-pro/",
        specs={
            "Category": "Tablet",
            "CPU": "Apple M4 (9-core CPU, 10-core GPU)",
            "RAM": "8GB Unified Memory",
            "Storage": "256GB SSD",
            "Display": "11-inch Tandem OLED Ultra Retina XDR, 120Hz ProMotion",
            "Battery": "31.29Wh (up to 10 hours)",
            "OS": "iPadOS",
            "Weight": "0.98 lbs"
        },
        description="Ultra-thin flagship tablet with a spectacular Tandem OLED display and the next-generation M4 processor.",
        pros=["State-of-the-art Tandem OLED display", "Super-fast Apple M4 processor", "Thinnest Apple product ever"],
        cons=["Extremely expensive", "Accessories (Keyboard, Pencil) sold separately"]
    ),
    Product(
        id="apple-ipad-10th-gen",
        name="iPad 10.9-inch (10th Gen)",
        brand="Apple",
        price=349.00,
        url="https://www.apple.com/ipad-10.9/",
        specs={
            "Category": "Tablet",
            "CPU": "Apple A14 Bionic",
            "RAM": "4GB RAM",
            "Storage": "64GB SSD",
            "Display": "10.9-inch Liquid Retina IPS (2360x1640)",
            "Battery": "28.6Wh (up to 10 hours)",
            "OS": "iPadOS",
            "Weight": "1.05 lbs"
        },
        description="The standard budget iPad with updated modern design, USB-C, and robust battery life, perfect for reading and media.",
        pros=["Great value-for-money iOS device", "Modern USB-C port", "Bright, colorful screen"],
        cons=["Only 64GB base storage", "Non-laminated display lacks anti-reflective coating"]
    ),
    Product(
        id="samsung-galaxy-tab-s9",
        name="Galaxy Tab S9 Wi-Fi",
        brand="Samsung",
        price=799.00,
        url="https://www.samsung.com/us/tablets/galaxy-tab-s9/",
        specs={
            "Category": "Tablet",
            "CPU": "Snapdragon 8 Gen 2 for Galaxy",
            "RAM": "8GB RAM",
            "Storage": "128GB (Expandable up to 1TB)",
            "Display": "11-inch Dynamic AMOLED 2X, 120Hz",
            "Battery": "8400mAh (up to 12 hours)",
            "OS": "Android 13 with One UI",
            "Weight": "1.1 lbs"
        },
        description="Premium Android tablet featuring a gorgeous 120Hz AMOLED screen, IP68 water resistance, and an included S Pen.",
        pros=["Stunning Dynamic AMOLED 120Hz display", "Included S Pen stylus in the box", "IP68 dust and water resistance"],
        cons=["DeX mode has learning curve", "Fewer tablet-optimized Android applications"]
    ),
    Product(
        id="samsung-galaxy-tab-a9-plus",
        name="Galaxy Tab A9+ Wi-Fi",
        brand="Samsung",
        price=219.00,
        url="https://www.samsung.com/us/tablets/galaxy-tab-a9-plus/",
        specs={
            "Category": "Tablet",
            "CPU": "Snapdragon 695 (8 Cores)",
            "RAM": "4GB RAM",
            "Storage": "64GB (Expandable)",
            "Display": "11-inch LCD (1920x1200), 90Hz",
            "Battery": "7040mAh (up to 9 hours)",
            "OS": "Android 13",
            "Weight": "1.06 lbs"
        },
        description="Affordable tablet great for children, students, and media consumption. Offers split-screen multitasking and 90Hz display.",
        pros=["Very affordable pricing", "Smooth 90Hz refresh rate screen", "Quad speakers with Dolby Atmos"],
        cons=["Average performance limits heavy gaming", "Chassis gets warm under workload"]
    ),
    # --- SMARTPHONES ---
    Product(
        id="apple-iphone-15",
        name="iPhone 15",
        brand="Apple",
        price=799.00,
        url="https://www.apple.com/iphone-15/",
        specs={
            "Category": "Smartphone",
            "CPU": "Apple A16 Bionic (6 Cores)",
            "RAM": "6GB RAM",
            "Storage": "128GB",
            "Display": "6.1-inch Super Retina XDR OLED",
            "Battery": "3349mAh (up to 20 hours video)",
            "OS": "iOS 17",
            "Weight": "0.38 lbs"
        },
        description="Standard iPhone with A16 processor, upgraded 48MP main camera, Dynamic Island notch, and USB-C connection.",
        pros=["Dynamic Island is highly functional", "Excellent 48MP main camera", "USB-C port standard"],
        cons=["Display limited to 60Hz", "Slow charging speeds"]
    ),
    Product(
        id="google-pixel-8",
        name="Pixel 8",
        brand="Google",
        price=699.00,
        url="https://store.google.com/product/pixel_8",
        specs={
            "Category": "Smartphone",
            "CPU": "Google Tensor G3",
            "RAM": "8GB LPDDR5X",
            "Storage": "128GB UFS 3.1",
            "Display": "6.2-inch OLED, 120Hz",
            "Battery": "4575mAh (up to 24 hours)",
            "OS": "Android 14 (7 years support)",
            "Weight": "0.41 lbs"
        },
        description="AI-centric smartphone with Google's custom Tensor G3 silicon. Best-in-class camera processing and extensive 7-year update guarantee.",
        pros=["Top-tier camera system with AI magic eraser", "Fluid 120Hz OLED screen", "7 years of OS upgrades"],
        cons=["Tensor G3 gets warm during heavy gaming", "Battery charging is slow"]
    ),
    Product(
        id="google-pixel-8a",
        name="Pixel 8a",
        brand="Google",
        price=499.00,
        url="https://store.google.com/product/pixel_8a",
        specs={
            "Category": "Smartphone",
            "CPU": "Google Tensor G3",
            "RAM": "8GB LPDDR5X",
            "Storage": "128GB",
            "Display": "6.1-inch OLED, 120Hz",
            "Battery": "4492mAh",
            "OS": "Android 14",
            "Weight": "0.41 lbs"
        },
        description="High-value mid-range phone containing the same flagship Tensor G3 chip, AI capabilities, and 120Hz display.",
        pros=["Flagship processor at budget pricing", "Exceptional camera quality", "Clean stock Android software"],
        cons=["Bezels are thick", "Plastic backing feels less premium"]
    ),
    Product(
        id="samsung-galaxy-s24",
        name="Galaxy S24",
        brand="Samsung",
        price=799.00,
        url="https://www.samsung.com/us/smartphones/galaxy-s24/",
        specs={
            "Category": "Smartphone",
            "CPU": "Snapdragon 8 Gen 3 for Galaxy",
            "RAM": "8GB LPDDR5X",
            "Storage": "128GB UFS 4.0",
            "Display": "6.2-inch Dynamic AMOLED 2X, 120Hz",
            "Battery": "4000mAh",
            "OS": "Android 14 with One UI",
            "Weight": "0.37 lbs"
        },
        description="Compact premium flagship with Snapdragon 8 Gen 3, advanced Galaxy AI software suite, and extremely bright display.",
        pros=["Top-tier Snapdragon performance", "Brilliant Dynamic AMOLED screen", "Packed with Galaxy AI features"],
        cons=["Base model has only 8GB RAM", "Camera zoom is average compared to Ultra"]
    ),
    # --- AUDIO / HEADPHONES ---
    Product(
        id="sony-wh-1000xm5",
        name="WH-1000XM5 ANC Headphones",
        brand="Sony",
        price=399.00,
        url="https://www.sony.com/electronics/headband-headphones/wh-1000xm5",
        specs={
            "Category": "Audio",
            "Drivers": "30mm Dynamic",
            "Battery Life": "Up to 30 hours (ANC on)",
            "ANC": "Industry-leading Dual Processor",
            "Connectivity": "Bluetooth 5.2, Multipoint",
            "Codecs": "LDAC, AAC, SBC",
            "Weight": "0.55 lbs"
        },
        description="Industry gold standard for noise canceling headphones. Supreme comfort, crystal-clear microphone, and rich customizable EQ.",
        pros=["Unmatched Active Noise Cancellation", "Extremely comfortable lightweight design", "LDAC hi-res audio support"],
        cons=["Do not fold flat like previous XM4s", "Touch controls can be touchy in cold weather"]
    ),
    Product(
        id="bose-qc-ultra",
        name="QuietComfort Ultra Headphones",
        brand="Bose",
        price=429.00,
        url="https://www.bose.com/p/headphones/bose-quietcomfort-ultra-headphones/QCUH-HEADPHONEWD.html",
        specs={
            "Category": "Audio",
            "Battery Life": "Up to 24 hours",
            "ANC": "Bose Custom CustomTune Technology",
            "Connectivity": "Bluetooth 5.3, Multipoint",
            "Audio Mode": "Immersive Spatial Audio",
            "Weight": "0.56 lbs"
        },
        description="Bose's premier headphones featuring immersive spatial audio, class-leading physical comfort, and stellar ANC.",
        pros=["Incredible physical comfort and earcups", "Superb active noise reduction", "Foldable travel-friendly design"],
        cons=["High premium price point", "App interface is occasionally slow"]
    ),
    Product(
        id="anker-soundcore-life-q30",
        name="Soundcore Life Q30",
        brand="Anker",
        price=79.99,
        url="https://us.soundcore.com/products/a3028",
        specs={
            "Category": "Audio",
            "Battery Life": "Up to 40 hours (ANC on)",
            "ANC": "Hybrid Active Noise Cancelling",
            "Connectivity": "Bluetooth 5.0, NFC",
            "Weight": "0.58 lbs"
        },
        description="Stellar budget headphones offering hybrid active noise cancellation, custom EQ app, and mammoth 40-hour battery life.",
        pros=["Extremely affordable with ANC", "Impressive 40-hour battery runtime", "Highly bass-rich dynamic profile"],
        cons=["Microphone quality is average", "Plastic hinges feel fragile"]
    ),
    # --- MONITORS ---
    Product(
        id="dell-ultrasharp-u2723qe",
        name="UltraSharp 27 4K USB-C Hub Monitor",
        brand="Dell",
        price=599.00,
        url="https://www.dell.com/en-us/shop/dell-ultrasharp-27-4k-usb-c-hub-monitor-u2723qe/spd/u2723qe-monitor",
        specs={
            "Category": "Monitor",
            "Size": "27-inch IPS Black Technology",
            "Resolution": "4K UHD (3840x2160)",
            "Aspect Ratio": "16:9",
            "Refresh Rate": "60Hz",
            "Ports": "USB-C (90W PD), DisplayPort 1.4, HDMI, RJ45 Ethernet",
            "Contrast Ratio": "2000:1"
        },
        description="Premium productivity monitor with IPS Black technology offering twice the contrast of normal monitors, built-in USB-C docking hub.",
        pros=["IPS Black offers incredible contrast and blacks", "Built-in 90W USB-C charging dock", "Daisy-chaining capability"],
        cons=["Limited to 60Hz refresh rate (not for fast gaming)"]
    ),
    Product(
        id="asus-tuf-vg27aq",
        name="TUF Gaming 27 WQHD Monitor",
        brand="ASUS",
        price=279.00,
        url="https://www.asus.com/us/displays-desktops/monitors/tuf-gaming/tuf-gaming-vg27aq/",
        specs={
            "Category": "Monitor",
            "Size": "27-inch IPS",
            "Resolution": "WQHD 2K (2560x1440)",
            "Refresh Rate": "165Hz",
            "Response Time": "1ms (MPRT)",
            "Sync Tech": "G-SYNC Compatible, FreeSync"
        },
        description="Stellar IPS gaming monitor offering a fast 165Hz refresh rate, 1440p resolution, and premium motion blur reduction.",
        pros=["Smooth 165Hz gaming experience", "G-Sync compatibility minimizes screen tearing", "IPS panel has great color accuracy"],
        cons=["HDR peak brightness is low", "Chunky gaming-oriented stand design"]
    )
]

@mcp.tool()
def search_products(query: str, max_price: Optional[float] = None) -> List[dict]:
    """
    Search for laptops in the database based on a search term (e.g. brand, CPU, specs) and price limit.
    
    Args:
        query: The search term (e.g. 'lenovo', 'oled', 'macbook', 'programming'). Use empty string '' to list all.
        max_price: Optional maximum price filter in USD.
    """
    logger.info(f"search_products called with query='{query}', max_price={max_price}")
    
    query_lower = query.lower()
    results = []
    
    for product in PRODUCTS_DB:
        # Check price filter
        if max_price is not None and product.price > max_price:
            continue
            
        # Match keywords in name, brand, description, or specs
        matches_query = (
            query_lower in product.name.lower() or
            query_lower in product.brand.lower() or
            query_lower in product.description.lower() or
            any(query_lower in str(val).lower() for val in product.specs.values())
        )
        
        # Check if the query contains general category intents or keywords
        if not matches_query:
            category_mapping = {
                "laptop": ["laptop", "notebook", "computer", "programming", "coder", "developer"],
                "tablet": ["tablet", "tab", "ipad"],
                "smartphone": ["phone", "smartphone", "iphone", "pixel", "galaxy", "mobile"],
                "audio": ["audio", "headphones", "earbuds", "noise canceling", "anc", "music"],
                "monitor": ["monitor", "display", "screen"]
            }
            product_category = product.specs.get("Category", "").lower()
            for cat, keywords in category_mapping.items():
                if product_category == cat and any(kw in query_lower for kw in keywords):
                    matches_query = True
                    break
            
        if matches_query or not query:
            results.append(product.model_dump())
            
    # Sort results by price (ascending)
    results.sort(key=lambda x: x["price"])
    return results

@mcp.tool()
def get_product_details(product_id: str) -> Optional[dict]:
    """
    Retrieve full details, specifications, and pros/cons for a specific product by its ID.
    
    Args:
        product_id: The unique product ID (e.g., 'lenovo-thinkpad-e14').
    """
    logger.info(f"get_product_details called with product_id='{product_id}'")
    for product in PRODUCTS_DB:
        if product.id == product_id:
            return product.model_dump()
    return None

@mcp.tool()
def compare_products(product_ids: List[str]) -> dict:
    """
    Compare multiple products side-by-side. Returns a dictionary containing comparative specifications.
    
    Args:
        product_ids: A list of product IDs to compare (e.g. ['lenovo-thinkpad-e14', 'acer-swift-go-14']).
    """
    logger.info(f"compare_products called with product_ids={product_ids}")
    
    selected_products = []
    for pid in product_ids:
        for product in PRODUCTS_DB:
            if product.id == pid:
                selected_products.append(product)
                break
                
    if not selected_products:
        return {"error": "No matching products found for the provided IDs."}
        
    # Get all spec keys across selected products
    all_spec_keys = set()
    for p in selected_products:
        all_spec_keys.update(p.specs.keys())
    all_spec_keys = sorted(list(all_spec_keys))
    
    comparison_table = {}
    for key in all_spec_keys:
        comparison_table[key] = {p.name: p.specs.get(key, "N/A") for p in selected_products}
        
    # Add pricing, pros, cons to comparison
    comparison_table["Price"] = {p.name: f"${p.price:.2f}" for p in selected_products}
    comparison_table["Product Page"] = {p.name: p.url for p in selected_products}
    comparison_table["Pros for Coding"] = {p.name: p.pros for p in selected_products}
    comparison_table["Cons for Coding"] = {p.name: p.cons for p in selected_products}
    
    return {
        "products": [p.model_dump() for p in selected_products],
        "comparison": comparison_table
    }

if __name__ == "__main__":
    # We run the FastMCP server over streamable-http as requested
    import sys
    port = 8081
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
        
    logger.info(f"Starting Product Research MCP Server on port {port}...")
    mcp.settings.host = "0.0.0.0"
    mcp.settings.port = port
    mcp.run(transport="sse")
