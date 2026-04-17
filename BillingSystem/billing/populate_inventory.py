"""
Script to populate the inventory with diverse products for various business types.
Useful for demo systems and initial data population.
"""
from BillingSystem.billing.models import Product
from decimal import Decimal


def populate_inventory(business_type=None):
    """
    Populates database with inventory items for different business types.
    Returns a tuple of (count, message) with the number of items added and a status message.
    """
    products_data = []

    # ===== ELECTRICAL SHOP =====
    electrical_items = [
        # Consumer Electronics
        ('LED TV 32 inch', 15000, '8528', 18, 50),
        ('LED TV 43 inch', 25000, '8528', 18, 30),
        ('LED TV 55 inch', 40000, '8528', 18, 20),
        ('Washing Machine 6kg', 12000, '8450', 18, 25),
        ('Washing Machine 7kg Front Load', 25000, '8450', 18, 15),
        ('Refrigerator 190L', 18000, '8418', 18, 20),
        ('Refrigerator 265L Double Door', 28000, '8418', 18, 15),
        ('Air Conditioner 1 Ton', 28000, '8415', 28, 12),
        ('Air Conditioner 1.5 Ton', 35000, '8415', 28, 10),
        ('Microwave Oven 20L', 6500, '8516', 18, 30),
        ('Electric Iron', 800, '8516', 18, 100),
        ('Mixer Grinder', 3500, '8509', 18, 40),
        ('Ceiling Fan 1200mm', 1500, '8414', 12, 80),
        ('Table Fan', 800, '8414', 12, 100),
        ('Water Heater 15L', 6500, '8516', 18, 25),

        # Electrical Components
        ('MCB 16A Single Pole', 120, '8536', 18, 200),
        ('MCB 32A Double Pole', 280, '8536', 18, 150),
        ('RCCB 32A 30mA', 850, '8536', 18, 100),
        ('Distribution Board 4 Way', 450, '8536', 18, 80),
        ('Distribution Board 8 Way', 850, '8536', 18, 60),
        ('Modular Socket 6A', 85, '8536', 18, 500),
        ('Modular Switch 10A', 90, '8536', 18, 500),
        ('Extension Board 4 Socket', 250, '8536', 18, 200),
        ('Voltage Stabilizer 5KVA', 4500, '8504', 18, 30),

        # Lighting
        ('LED Bulb 9W', 85, '8539', 12, 1000),
        ('LED Bulb 12W', 120, '8539', 12, 800),
        ('LED Tube Light 18W 4ft', 220, '8539', 12, 500),
        ('LED Tube Light 36W 8ft', 420, '8539', 12, 300),
        ('LED Panel Light 18W', 450, '8539', 12, 200),
        ('LED Panel Light 36W', 750, '8539', 12, 150),
        ('LED Street Light 50W', 1800, '8539', 12, 100),
        ('CFL 20W', 150, '8539', 12, 400),

        # Wiring & Cables
        ('House Wire 1.5mm 90m', 850, '8544', 18, 200),
        ('House Wire 2.5mm 90m', 1400, '8544', 18, 150),
        ('House Wire 4mm 90m', 2200, '8544', 18, 100),
        ('Flexible Cable 3 Core 1.5mm 100m', 1800, '8544', 18, 80),
        ('Armoured Cable 4 Core 6mm 100m', 8500, '8544', 18, 40),
        ('Switchboard Wire 1mm 100m', 450, '8544', 18, 150),
    ]

    # ===== COMPUTER & IT SHOP =====
    computer_items = [
        # Desktop Components
        ('Intel Core i5 13th Gen Processor', 18000, '8542', 18, 30),
        ('Intel Core i7 13th Gen Processor', 32000, '8542', 18, 20),
        ('AMD Ryzen 5 5600X Processor', 15000, '8542', 18, 25),
        ('ASUS TUF B550M Motherboard', 9500, '8473', 18, 35),
        ('MSI MAG B660M Motherboard', 12000, '8473', 18, 30),
        ('Corsair 16GB DDR4 3200MHz RAM', 4500, '8473', 18, 100),
        ('Kingston 32GB DDR4 RAM Kit', 8500, '8473', 18, 50),
        ('NVIDIA RTX 3060 12GB Graphics Card', 35000, '8473', 18, 20),
        ('NVIDIA RTX 4070 12GB Graphics Card', 55000, '8473', 18, 15),
        ('AMD RX 6600 XT Graphics Card', 28000, '8473', 18, 18),
        ('Samsung 500GB NVMe SSD', 4200, '8471', 18, 80),
        ('WD 1TB NVMe SSD', 7500, '8471', 18, 60),
        ('Seagate 2TB HDD', 4800, '8471', 18, 100),
        ('WD 4TB HDD', 8500, '8471', 18, 50),
        ('Corsair 650W PSU 80+ Bronze', 5200, '8504', 18, 40),
        ('Cooler Master 750W PSU 80+ Gold', 8500, '8504', 18, 30),
        ('NZXT H510 Cabinet', 5500, '8473', 18, 25),
        ('Cooler Master TD500 RGB Cabinet', 8500, '8473', 18, 20),

        # Laptops
        ('HP 15s Ryzen 5 8GB 512GB Laptop', 42000, '8471', 18, 15),
        ('Dell Inspiron i5 11th Gen 16GB Laptop', 55000, '8471', 18, 12),
        ('Lenovo IdeaPad i7 16GB 1TB Laptop', 68000, '8471', 18, 10),
        ('ASUS TUF Gaming Ryzen 7 16GB Laptop', 75000, '8471', 18, 8),
        ('MacBook Air M2 8GB 256GB', 99000, '8471', 18, 5),

        # Peripherals
        ('Logitech MK235 Wireless Keyboard Mouse', 1500, '8471', 18, 100),
        ('Logitech G502 Gaming Mouse', 3500, '8471', 18, 50),
        ('Razer DeathAdder V2 Gaming Mouse', 4200, '8471', 18, 40),
        ('Logitech K380 Bluetooth Keyboard', 2200, '8471', 18, 60),
        ('Corsair K70 RGB Mechanical Keyboard', 9500, '8471', 18, 25),
        ('ViewSonic 24" Full HD Monitor', 9500, '8528', 18, 40),
        ('LG 27" QHD IPS Monitor', 18000, '8528', 18, 25),
        ('Samsung 32" 4K Monitor', 28000, '8528', 18, 15),
        ('HP LaserJet M126nw Printer', 12500, '8443', 18, 20),
        ('Canon Pixma G3000 Printer', 9500, '8443', 18, 30),
        ('Epson EcoTank L3250 Printer', 14000, '8443', 18, 25),

        # Networking
        ('TP-Link AC1200 WiFi Router', 1200, '8517', 18, 80),
        ('ASUS RT-AX55 WiFi 6 Router', 6500, '8517', 18, 30),
        ('Netgear 8-Port Gigabit Switch', 2800, '8517', 18, 50),
        ('TP-Link 24-Port PoE Switch', 18000, '8517', 18, 15),
        ('Cat6 UTP Cable 305m Box', 4500, '8544', 18, 40),

        # Software Licenses
        ('Windows 11 Pro License', 15000, '9984', 18, 100),
        ('Microsoft Office 2021 Home & Business', 22000, '9984', 18, 80),
        ('Adobe Creative Cloud 1 Year', 45000, '9984', 18, 30),
        ('Kaspersky Total Security 3 Device', 1800, '9984', 18, 150),
        ('Norton 360 Premium 5 Device', 2500, '9984', 18, 100),
    ]

    # ===== AUTO GARAGE/WORKSHOP =====
    garage_items = [
        # Engine Parts
        ('Engine Oil 5W-30 5L', 2500, '2710', 28, 100),
        ('Engine Oil 10W-40 5L', 1800, '2710', 28, 120),
        ('Oil Filter Universal', 280, '8421', 28, 200),
        ('Air Filter Universal', 350, '8421', 28, 180),
        ('Fuel Filter', 220, '8421', 28, 150),
        ('Spark Plug Set (4pcs)', 850, '8511', 28, 100),
        ('Spark Plug Iridium (4pcs)', 2800, '8511', 28, 50),
        ('Timing Belt Kit', 3500, '4010', 28, 60),
        ('Serpentine Belt', 1200, '4010', 28, 80),
        ('Radiator Coolant 5L', 850, '3820', 18, 100),
        ('Radiator Cap', 180, '8708', 28, 200),
        ('Thermostat', 450, '8708', 28, 100),
        ('Water Pump', 2800, '8413', 28, 40),
        ('Alternator', 5500, '8511', 28, 25),
        ('Starter Motor', 4500, '8511', 28, 30),
        ('Car Battery 12V 65Ah', 5500, '8507', 28, 40),
        ('Car Battery 12V 100Ah', 9500, '8507', 28, 25),

        # Brake & Suspension
        ('Brake Pad Set Front', 1800, '8708', 28, 80),
        ('Brake Pad Set Rear', 1500, '8708', 28, 80),
        ('Brake Disc Front Pair', 3500, '8708', 28, 50),
        ('Brake Disc Rear Pair', 2800, '8708', 28, 50),
        ('Brake Fluid DOT 4 500ml', 280, '3819', 18, 150),
        ('Shock Absorber Front Pair', 4500, '8708', 28, 40),
        ('Shock Absorber Rear Pair', 3800, '8708', 28, 40),
        ('Suspension Spring Front', 2200, '8708', 28, 35),

        # Body Parts
        ('Side Mirror Left', 1200, '8708', 28, 50),
        ('Side Mirror Right', 1200, '8708', 28, 50),
        ('Headlight Assembly Left', 4500, '8512', 28, 30),
        ('Headlight Assembly Right', 4500, '8512', 28, 30),
        ('Tail Light Assembly', 2200, '8512', 28, 40),
        ('Front Bumper', 6500, '8708', 28, 20),
        ('Rear Bumper', 5500, '8708', 28, 20),
        ('Bonnet', 8500, '8708', 28, 15),
        ('Front Fender', 3500, '8708', 28, 25),
        ('Door Panel Front', 12000, '8708', 28, 15),

        # Tires & Wheels
        ('Car Tire 175/65 R14', 3500, '4011', 28, 80),
        ('Car Tire 195/65 R15', 4500, '4011', 28, 70),
        ('SUV Tire 235/65 R17', 8500, '4011', 28, 50),
        ('Alloy Wheel 14 inch', 2800, '8708', 28, 60),
        ('Alloy Wheel 16 inch', 4500, '8708', 28, 40),
        ('Steel Wheel 15 inch', 1500, '8708', 28, 80),
        ('Wheel Alignment Service', 800, '9987', 18, 0),
        ('Wheel Balancing', 400, '9987', 18, 0),

        # Tools & Equipment
        ('Hydraulic Jack 2 Ton', 2800, '8425', 18, 25),
        ('Hydraulic Jack 3 Ton', 4500, '8425', 18, 20),
        ('Air Compressor 50L', 8500, '8414', 18, 15),
        ('Impact Wrench', 5500, '8467', 18, 20),
        ('Socket Set 46pcs', 2800, '8204', 18, 30),
        ('Wrench Set 12pcs', 1500, '8204', 18, 50),
        ('Screwdriver Set 32pcs', 850, '8205', 18, 60),
        ('Car Vacuum Cleaner', 1800, '8508', 18, 40),
        ('Pressure Washer', 8500, '8424', 18, 15),
    ]

    # ===== MEDICAL / PHARMACY =====
    medical_items = [
        # Medicines (prescription & OTC)
        ('Paracetamol 500mg Tablets (10s)', 12, '3004', 12, 2000),
        ('Ibuprofen 400mg Tablets (10s)', 18, '3004', 12, 1500),
        ('Amoxicillin 500mg Capsules (10s)', 85, '3004', 12, 800),
        ('Cetirizine 10mg Tablets (10s)', 28, '3004', 12, 1200),
        ('Azithromycin 500mg Tablets (3s)', 95, '3004', 12, 600),
        ('Omeprazole 20mg Capsules (10s)', 45, '3004', 12, 1000),
        ('Metformin 500mg Tablets (10s)', 32, '3004', 12, 1500),
        ('Atorvastatin 10mg Tablets (10s)', 85, '3004', 12, 800),
        ('Levothyroxine 50mcg Tablets (10s)', 42, '3004', 12, 900),
        ('Multivitamin Tablets (30s)', 280, '3004', 12, 500),
        ('Vitamin D3 60K Capsules', 45, '3004', 12, 1000),
        ('Calcium + Vitamin D Tablets (15s)', 120, '3004', 12, 800),
        ('Cough Syrup 100ml', 85, '3004', 5, 1200),
        ('Antacid Syrup 200ml', 95, '3004', 12, 1000),
        ('Pain Relief Gel 30g', 120, '3004', 18, 800),
        ('Antiseptic Cream 20g', 65, '3004', 18, 1000),

        # Medical Equipment
        ('Digital Thermometer', 180, '9018', 12, 500),
        ('Blood Pressure Monitor Digital', 1500, '9018', 12, 200),
        ('Pulse Oximeter', 850, '9018', 12, 300),
        ('Glucometer with 25 Strips', 650, '9018', 12, 250),
        ('Nebulizer Machine', 1800, '9019', 12, 150),
        ('Stethoscope', 850, '9018', 12, 200),
        ('Infrared Thermometer', 1200, '9025', 12, 180),
        ('Weighing Scale Digital', 850, '9016', 18, 150),
        ('Hot Water Bag', 120, '4014', 18, 400),
        ('Ice Pack', 85, '9619', 18, 500),
        ('Steam Inhaler', 450, '9019', 18, 200),

        # First Aid & Medical Supplies
        ('First Aid Kit Complete', 850, '9619', 12, 300),
        ('Bandage Roll 10cm x 4m', 28, '3005', 12, 1000),
        ('Gauze Pads Sterile 100pcs', 180, '3005', 12, 500),
        ('Cotton Balls 100g', 35, '5601', 12, 800),
        ('Cotton Applicator 100pcs', 42, '5601', 12, 600),
        ('Medical Tape 1 inch', 45, '3005', 18, 800),
        ('Surgical Gloves Latex L (100pcs)', 380, '4015', 12, 400),
        ('Surgical Mask 3-ply (50pcs)', 120, '6307', 12, 1000),
        ('N95 Mask (10pcs)', 280, '6307', 12, 500),
        ('Hand Sanitizer 500ml', 120, '3401', 18, 800),
        ('Hydrogen Peroxide 100ml', 28, '2847', 18, 1000),
        ('Betadine Solution 100ml', 95, '3004', 18, 600),
        ('Dettol Antiseptic 550ml', 180, '3401', 18, 500),
        ('Syringe 5ml Disposable (100pcs)', 280, '9018', 12, 400),
        ('IV Cannula 20G (25pcs)', 380, '9018', 12, 300),
    ]

    # ===== RESTAURANT / CAFÉ =====
    restaurant_items = [
        # Kitchen Equipment
        ('Commercial Gas Stove 4 Burner', 18000, '7321', 18, 15),
        ('Commercial Induction Cooktop', 12000, '8516', 18, 20),
        ('Commercial Microwave 34L', 22000, '8516', 18, 10),
        ('Deep Fryer 8L', 15000, '8516', 18, 12),
        ('Commercial Mixer Grinder', 8500, '8509', 18, 18),
        ('Food Processor 3L', 12000, '8509', 18, 15),
        ('Commercial Refrigerator 350L', 45000, '8418', 18, 10),
        ('Display Refrigerator Glass Door', 55000, '8418', 18, 8),
        ('Chest Freezer 200L', 28000, '8418', 18, 12),
        ('Water Purifier RO Commercial', 18000, '8421', 18, 15),
        ('Coffee Machine Commercial', 45000, '8516', 18, 8),
        ('Espresso Machine', 65000, '8516', 18, 5),
        ('Juice Extractor', 8500, '8509', 18, 12),
        ('Toaster 4 Slice Commercial', 5500, '8516', 18, 20),
        ('Sandwich Maker Commercial', 4500, '8516', 18, 18),
        ('Hot Plate Electric', 2800, '8516', 18, 25),
        ('Food Warmer Display', 18000, '8516', 18, 10),
        ('Commercial Oven', 45000, '8514', 18, 8),

        # Cookware
        ('Stainless Steel Kadai 3L', 850, '7323', 12, 50),
        ('Stainless Steel Kadai 5L', 1200, '7323', 12, 40),
        ('Non-Stick Tawa 12 inch', 650, '7323', 18, 60),
        ('Pressure Cooker 5L', 1500, '7323', 18, 40),
        ('Pressure Ccoker 10L', 2800, '7323', 18, 25),
        ('Sauce Pan Set 3pcs', 1800, '7323', 18, 35),
        ('Frying Pan 10 inch', 650, '7323', 18, 50),
        ('Stock Pot 20L', 3500, '7323', 18, 20),
        ('Mixing Bowl Set SS 5pcs', 850, '7323', 18, 40),

        # Tableware & Serving
        ('Dinner Plate Ceramic Set 6pcs', 850, '6911', 12, 80),
        ('Quarter Plate Set 6pcs', 550, '6911', 12, 100),
        ('Glass Tumbler Set 6pcs', 280, '7013', 18, 150),
        ('Wine Glass Set 6pcs', 650, '7013', 18, 80),
        ('Coffee Mug Set 6pcs', 450, '6911', 18, 120),
        ('Stainless Steel Thali Set 6pcs', 1200, '7323', 18, 60),
        ('Serving Bowl SS 3pcs', 850, '7323', 18, 70),
        ('Serving Tray SS Large', 550, '7323', 18, 50),
        ('Cutlery Set 24pcs SS', 1500, '8215', 18, 60),
        ('Spoon Set 12pcs SS', 450, '8215', 18, 100),
        ('Knife Set Chef 6pcs', 1800, '8211', 18, 40),
        ('Chopping Board Set 3pcs', 650, '3926', 18, 80),

        # Disposables
        ('Paper Plate 10 inch (100pcs)', 180, '4823', 12, 200),
        ('Paper Cup 200ml (100pcs)', 120, '4823', 18, 300),
        ('Tissue Paper Napkin (100pcs)', 85, '4818', 18, 400),
        ('Aluminum Foil Roll 18m', 280, '7607', 18, 150),
        ('Cling Film Roll 30m', 180, '3920', 18, 200),
        ('Plastic Spoon (100pcs)', 65, '3924', 18, 300),
        ('Plastic Fork (100pcs)', 65, '3924', 18, 300),
        ('Food Container Plastic 500ml (25pcs)', 280, '3924', 18, 150),
        ('Takeaway Box Large (50pcs)', 350, '4823', 18, 120),
    ]

    # ===== CLOTHING / FASHION =====
    fashion_items = [
        # Men's Apparel
        ('Men Cotton T-Shirt', 350, '6109', 5, 200),
        ('Men Polo T-Shirt', 550, '6105', 5, 150),
        ('Men Formal Shirt', 850, '6205', 5, 120),
        ('Men Casual Shirt', 650, '6205', 5, 150),
        ('Men Denim Jeans', 1200, '6203', 5, 100),
        ('Men Chinos Trousers', 950, '6203', 5, 120),
        ('Men Track Pants', 550, '6203', 12, 150),
        ('Men Shorts', 450, '6203', 12, 180),
        ('Men Sweatshirt Hoodie', 850, '6110', 12, 100),
        ('Men Blazer', 2800, '6203', 12, 40),
        ('Men Suit 2-Piece', 5500, '6203', 12, 25),

        # Women's Apparel
        ('Women Cotton Kurti', 650, '6206', 5, 150),
        ('Women Designer Kurti', 1200, '6206', 5, 100),
        ('Women Palazzo Pants', 550, '6204', 5, 120),
        ('Women Leggings', 280, '6204', 5, 250),
        ('Women Salwar Suit Dress Material', 1500, '6204', 5, 80),
        ('Women Saree Cotton', 850, '6204', 5, 100),
        ('Women Saree Silk', 2500, '6204', 5, 50),
        ('Women Western Top', 650, '6206', 5, 150),
        ('Women Jeans', 950, '6204', 5, 120),
        ('Women One-Piece Dress', 1200, '6204', 12, 80),
        ('Women Ethnic Gown', 1800, '6204', 12, 60),

        # Kids Apparel
        ('Kids T-Shirt (2-8 Years)', 250, '6109', 5, 200),
        ('Kids Frock Dress', 450, '6209', 5, 150),
        ('Kids Shorts Set', 350, '6209', 5, 180),
        ('Kids Jeans', 550, '6209', 5, 120),
        ('Kids School Uniform Shirt', 350, '6209', 5, 200),
        ('Kids School Uniform Pants', 450, '6209', 5, 180),

        # Footwear
        ('Men Casual Shoes', 1200, '6403', 12, 80),
        ('Men Formal Shoes', 1500, '6403', 12, 60),
        ('Men Sports Shoes', 1800, '6404', 18, 100),
        ('Men Slippers', 280, '6404', 12, 200),
        ('Men Sandals', 550, '6403', 12, 150),
        ('Women Casual Shoes', 950, '6403', 12, 100),
        ('Women Heels', 1200, '6403', 12, 80),
        ('Women Flats', 650, '6403', 12, 120),
        ('Women Sandals', 550, '6404', 12, 150),
        ('Kids School Shoes', 650, '6403', 12, 120),
        ('Kids Sports Shoes', 850, '6404', 18, 100),

        # Accessories
        ('Men Leather Belt', 450, '4203', 18, 150),
        ('Men Wallet Leather', 550, '4202', 18, 120),
        ('Men Watch Analog', 1200, '9102', 18, 60),
        ('Men Watch Digital', 850, '9102', 18, 80),
        ('Men Socks Pack of 3', 180, '6115', 12, 250),
        ('Women Handbag', 950, '4202', 18, 100),
        ('Women Purse', 450, '4202', 18, 150),
        ('Women Watch', 1500, '9102', 18, 60),
        ('Women Jewelry Set Artificial', 650, '7117', 3, 100),
        ('Sunglasses Men', 550, '9004', 18, 120),
        ('Sunglasses Women', 650, '9004', 18, 100),
        ('Cap Mens', 220, '6505', 12, 200),
        ('Scarf Women', 280, '6214', 5, 150),
    ]

    # Dictionary mapping business types to their item lists
    business_map = {
        'electrical': electrical_items,
        'computer': computer_items,
        'garage': garage_items,
        'medical': medical_items,
        'restaurant': restaurant_items,
        'fashion': fashion_items,
    }

    # ===== GROCERY STORE =====
    grocery_items = [
        ('Basmati Rice 5kg', 450, '1006', 5, 100),
        ('Wheat Flour 10kg', 380, '1101', 5, 80),
        ('Sugar 5kg', 220, '1701', 5, 100),
        ('Cooking Oil 5L', 750, '1508', 5, 60),
        ('Toor Dal 1kg', 160, '0713', 5, 150),
        ('Chana Dal 1kg', 120, '0713', 5, 150),
        ('Salt 1kg', 25, '2501', 5, 500),
        ('Tea 500g', 280, '0902', 5, 200),
        ('Coffee 200g', 350, '0901', 5, 150),
        ('Milk Powder 500g', 320, '0402', 5, 100),
        ('Ghee 1kg', 580, '0405', 12, 80),
        ('Butter 500g', 280, '0405', 12, 100),
        ('Paneer 200g', 90, '0406', 5, 150),
        ('Curd 400g', 45, '0403', 5, 200),
        ('Bread Loaf', 40, '1905', 5, 300),
        ('Biscuits Packet', 30, '1905', 18, 500),
        ('Noodles Pack', 25, '1902', 12, 400),
        ('Tomato Ketchup 500g', 120, '2103', 12, 150),
        ('Spices Combo Pack', 180, '0910', 5, 100),
        ('Pickle 500g', 95, '2001', 12, 120),
    ]
    business_map['grocery'] = grocery_items

    # ===== HARDWARE STORE =====
    hardware_items = [
        ('Hammer Claw 300g', 250, '8205', 18, 100),
        ('Screwdriver Set 6pc', 350, '8205', 18, 80),
        ('Pliers Combination 8inch', 280, '8203', 18, 100),
        ('Adjustable Wrench 10inch', 450, '8204', 18, 60),
        ('Measuring Tape 5m', 120, '9017', 18, 150),
        ('Spirit Level 2ft', 320, '9015', 18, 50),
        ('Hand Saw 18inch', 380, '8202', 18, 60),
        ('Drill Machine 10mm', 2500, '8467', 18, 30),
        ('Drill Bit Set', 450, '8207', 18, 50),
        ('Angle Grinder 4inch', 2200, '8467', 18, 25),
        ('Cutting Disc 4inch', 35, '6804', 18, 500),
        ('Sandpaper Sheet', 15, '6805', 18, 1000),
        ('Wood Screws Box 100pc', 180, '7318', 18, 200),
        ('Wall Plugs Pack 50pc', 80, '3926', 18, 300),
        ('Nails 2inch 500g', 60, '7317', 18, 400),
        ('PVC Pipe 1inch 10ft', 120, '3917', 18, 200),
        ('PVC Elbow 1inch', 25, '3917', 18, 500),
        ('Gate Valve 1inch', 350, '8481', 18, 80),
        ('Teflon Tape', 25, '3919', 18, 500),
        ('Adhesive Fevicol 500g', 180, '3506', 18, 150),
    ]
    business_map['hardware'] = hardware_items

    # ===== STATIONERY/OFFICE =====
    stationery_items = [
        ('A4 Paper Ream 500sheets', 350, '4802', 12, 100),
        ('Ballpoint Pen Pack 10', 80, '9608', 18, 300),
        ('Gel Pen Pack 5', 120, '9608', 18, 200),
        ('Pencil Pack 10', 50, '9609', 12, 400),
        ('Eraser Pack 5', 30, '4016', 18, 500),
        ('Sharpener Pack 5', 40, '8214', 18, 400),
        ('Notebook 200 pages', 80, '4820', 12, 300),
        ('Register 400 pages', 180, '4820', 12, 150),
        ('Folder File Pack 10', 150, '4820', 18, 200),
        ('Stapler Machine', 120, '8305', 18, 100),
        ('Stapler Pins Box', 25, '8305', 18, 500),
        ('Paper Clips Box 100', 35, '8305', 18, 400),
        ('Scissors 7inch', 80, '8213', 18, 150),
        ('Glue Stick Pack 3', 90, '3506', 18, 250),
        ('Fevistick Pack 5', 120, '3506', 18, 200),
        ('Ruler 12inch Pack 5', 60, '9017', 18, 300),
        ('Geometry Box', 150, '9017', 18, 100),
        ('Calculator Scientific', 450, '8470', 18, 50),
        ('Whiteboard Marker Set', 180, '9608', 18, 100),
        ('Sticky Notes Pack', 80, '4820', 18, 250),
    ]
    business_map['stationery'] = stationery_items

    # ===== BEAUTY/SALON =====
    beauty_items = [
        ('Shampoo 500ml', 280, '3305', 18, 150),
        ('Conditioner 200ml', 220, '3305', 18, 120),
        ('Hair Oil 200ml', 180, '3305', 18, 150),
        ('Hair Gel 100g', 120, '3305', 18, 200),
        ('Hair Color Kit', 350, '3305', 18, 80),
        ('Face Wash 100ml', 180, '3304', 18, 150),
        ('Face Cream 50g', 280, '3304', 18, 100),
        ('Sunscreen 100ml', 350, '3304', 18, 80),
        ('Moisturizer 200ml', 320, '3304', 18, 100),
        ('Lipstick', 250, '3304', 18, 150),
        ('Nail Polish', 120, '3304', 18, 200),
        ('Makeup Kit', 850, '3304', 18, 40),
        ('Perfume 100ml', 650, '3303', 18, 60),
        ('Deodorant 150ml', 180, '3307', 18, 150),
        ('Body Lotion 200ml', 220, '3304', 18, 120),
        ('Facial Kit', 450, '3304', 18, 50),
        ('Hair Dryer', 1200, '8516', 18, 30),
        ('Hair Straightener', 1500, '8516', 18, 25),
        ('Trimmer', 800, '8510', 18, 40),
        ('Manicure Set', 350, '8214', 18, 60),
    ]
    business_map['beauty'] = beauty_items

    # ===== SPORTS/FITNESS =====
    sports_items = [
        ('Cricket Bat Kashmir Willow', 1200, '9506', 12, 40),
        ('Cricket Ball Leather', 350, '9506', 12, 100),
        ('Cricket Gloves Pair', 650, '9506', 12, 50),
        ('Cricket Pads Pair', 850, '9506', 12, 40),
        ('Football Size 5', 650, '9506', 12, 60),
        ('Basketball Size 7', 750, '9506', 12, 50),
        ('Volleyball', 450, '9506', 12, 60),
        ('Badminton Racket Pair', 550, '9506', 12, 50),
        ('Shuttlecock Pack 10', 180, '9506', 12, 100),
        ('Tennis Ball Pack 3', 250, '9506', 12, 80),
        ('Skipping Rope', 180, '9506', 12, 100),
        ('Yoga Mat', 450, '9506', 12, 60),
        ('Dumbbell 5kg Pair', 850, '9506', 12, 40),
        ('Resistance Band Set', 550, '9506', 12, 50),
        ('Gym Gloves', 350, '9506', 12, 80),
        ('Water Bottle Sports 1L', 280, '3924', 18, 100),
        ('Sports Bag', 650, '4202', 18, 50),
        ('Running Shoes', 1800, '6404', 18, 40),
        ('Track Suit', 1200, '6211', 12, 50),
        ('Sports T-Shirt', 450, '6109', 5, 100),
    ]
    business_map['sports'] = sports_items

    # ===== JEWELRY SHOP =====
    jewelry_items = [
        ('Gold Chain 22K 5g', 28000, '7113', 3, 20),
        ('Gold Ring 22K 3g', 17000, '7113', 3, 30),
        ('Gold Earrings 22K 4g', 22500, '7113', 3, 25),
        ('Gold Bangle 22K 10g', 56000, '7113', 3, 15),
        ('Gold Pendant 22K 2g', 11500, '7113', 3, 30),
        ('Silver Chain 50g', 4500, '7113', 3, 40),
        ('Silver Ring 10g', 950, '7113', 3, 60),
        ('Silver Anklet Pair 30g', 2800, '7113', 3, 35),
        ('Silver Bangle 25g', 2400, '7113', 3, 40),
        ('Diamond Ring 0.25ct', 35000, '7113', 3, 10),
        ('Diamond Earrings 0.5ct', 55000, '7113', 3, 8),
        ('Pearl Necklace', 8500, '7116', 3, 20),
        ('Artificial Jewelry Set', 850, '7117', 3, 100),
        ('Imitation Bangles Set 12pc', 350, '7117', 3, 150),
        ('Fashion Earrings', 250, '7117', 3, 200),
        ('Mangalsutra Gold 22K 8g', 45000, '7113', 3, 15),
        ('Nose Pin Gold', 3500, '7113', 3, 50),
        ('Toe Ring Silver Pair', 450, '7113', 3, 80),
        ('Watch Strap Gold Plated', 1200, '7113', 3, 40),
        ('Jewelry Box Velvet', 350, '4202', 18, 60),
    ]
    business_map['jewelry'] = jewelry_items

    # Determine items to add based on user input
    available_types = ', '.join(business_map.keys())

    if business_type:
        if business_type.lower() in business_map:
            all_items = business_map[business_type.lower()]
        else:
            return 0, f'Invalid business type: {business_type}. Available types: {available_types}'
    else:
        # If no type specified, add all items
        all_items = []
        for items in business_map.values():
            all_items.extend(items)

    # Create Product objects
    for name, price, hsn, gst_rate, stock in all_items:
        products_data.append(Product(
            name=name,
            price=Decimal(str(price)),
            hsn_code=hsn,
            gst_rate=Decimal(str(gst_rate)),
            stock=stock
        ))

    # Bulk create all products
    Product.objects.bulk_create(products_data, ignore_conflicts=True)

    return len(products_data), f'Successfully added {len(products_data)} inventory items!'
