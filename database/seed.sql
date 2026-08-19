-- Seed Data for E-Commerce Database

-- Categories
INSERT OR IGNORE INTO categories (id, name, slug, description, icon) VALUES
(1, 'Electronics & Gadgets', 'electronics-gadgets', 'Laptops, Smartphones, Smartwatches & Premium Tech Accessories', 'bi-laptop'),
(2, 'Audio & Sound', 'audio-sound', 'Wireless Earbuds, Noise-Cancelling Headphones & Hi-Fi Speakers', 'bi-headphones'),
(3, 'Wearable Tech', 'wearable-tech', 'Fitness Trackers, Smartbands & Premium Chronograph Smartwatches', 'bi-smartwatch'),
(4, 'Home & Living', 'home-living', 'Smart Appliances, Lighting & Modern Home Comfort', 'bi-house-door'),
(5, 'Fashion & Accessories', 'fashion-accessories', 'Designer Apparel, Luxury Backpacks & Eyewear', 'bi-bag-check');

-- Admin User
INSERT OR IGNORE INTO admin (id, name, email, password_hash) VALUES
(1, 'TechTrend Administrator', 'admin@techtrend.com', 'scrypt:32768:8:1$hU8u5e91JzL2XkPq$df57b42023fa54e5b7b15a6b0c2a71d18bbd7889e9000a6c384813583a48e7eb5a5ee5bbf7df51239f886f4a86181f5c6dbd9f7ad9c2d1b827e8a93e82710bb8');

-- Coupons
INSERT OR IGNORE INTO coupons (id, code, discount_type, discount_value, min_order_amount, max_discount, is_active) VALUES
(1, 'WELCOME10', 'percent', 10.00, 499.00, 500.00, 1),
(2, 'SAVE20', 'percent', 20.00, 1499.00, 1000.00, 1),
(3, 'FREESHIP', 'flat', 49.00, 299.00, 49.00, 1);

-- Sample Products
INSERT OR IGNORE INTO products (id, category_id, name, slug, short_description, description, specifications, price, discount_percent, stock, avg_rating, review_count, is_featured, is_trending, is_active) VALUES
(1, 1, 'ProBook Ultra 15 M3 Laptop', 'probook-ultra-15-m3', '15.6" Retina OLED display, 16GB RAM, 512GB NVMe SSD, M3 Octa-Core processor', 'Experience breathtaking speed and efficiency with the ProBook Ultra 15. Engineered for professionals, software developers, and creators. Features a vibrant 4K OLED HDR display, all-day 18-hour battery life, ultra-quiet cooling, and aluminum unibody design.', 'Processor: M3 8-Core CPU
RAM: 16GB LPDDR5X
Storage: 512GB PCIe 4.0 SSD
Display: 15.6 inch 3.2K OLED 120Hz
Battery: 78Wh (Up to 18 Hours)
Weight: 1.38 kg', 89999.00, 12.00, 25, 4.8, 14, 1, 1, 1),
(2, 2, 'AuraSound ANC Wireless Headphones', 'aurasound-anc-headphones', 'Active Noise Cancelling, 40-hour Playback, Hi-Res Audio certification with Spatial Sound', 'Immerse yourself in pure studio-grade audio quality with AuraSound ANC Headphones. Custom 40mm beryllium drivers deliver punchy bass, rich mids, and crystal-clear highs. Includes multi-device Bluetooth 5.3 connection.', 'Driver Size: 40mm Beryllium
Battery Life: 40 Hours (ANC On)
Charging: USB-C Fast Charge (10 min = 4 hrs)
Bluetooth: v5.3 Dual Connect
Active Noise Cancellation: Hybrid Active 45dB', 12999.00, 25.00, 40, 4.7, 28, 1, 1, 1),
(3, 3, 'ApexFit Pro Smartwatch', 'apexfit-pro-smartwatch', '1.43" AMOLED Display, SpO2 & Heart Rate Tracker, GPS, 100+ Sports Modes', 'Track your health and daily performance with surgical accuracy. Features continuous heart rate monitoring, sleep stage analysis, outdoor GPS navigation, water resistance up to 50 meters, and custom watch faces.', 'Display: 1.43" HD AMOLED (466x466)
Battery Life: 12 Days Typical Usage
Waterproof Rating: 5 ATM (50m)
Sensors: PPG Heart Rate, SpO2, Accelerometer, Gyro, GPS
Compatibility: Android & iOS', 4999.00, 30.00, 60, 4.6, 42, 1, 1, 1),
(4, 1, 'Nova tab 11 Pro Tablet', 'nova-tab-11-pro', '11" 120Hz Display, Octa-Core 2.8GHz, Stylus Support, 128GB Storage', 'The ultimate companion for note-taking, digital art, and video streaming. Includes low-latency stylus pen and quad stereo speakers tuned by Dolby Atmos.', 'Display: 11" 2.5K 120Hz IPS LCD
RAM / Storage: 8GB / 128GB (Expandable 1TB)
Processor: Snapdragon 870
Battery: 8600mAh 33W Fast Charging', 27999.00, 15.00, 18, 4.5, 19, 0, 1, 1),
(5, 2, 'PulseBuds Pro TWS Earbuds', 'pulsebuds-pro-tws', 'Transparency Mode, Quad Mics with ENC, IPX5 Water Resistant, 32hr Battery', 'Ultra-lightweight ergonomic earbuds delivering deep bass and crystal clear call quality. Features touch controls, auto-pairing, and ultra-low latency game mode.', 'Playback Time: 8h Earbuds + 24h Case
Bluetooth: v5.3
Water Resistance: IPX5 Splashproof
Noise Reduction: Environmental Noise Cancellation (ENC) for Calls', 2499.00, 40.00, 85, 4.4, 53, 1, 0, 1),
(6, 4, 'AuraGlow Smart Desk Lamp', 'auraglow-smart-desk-lamp', 'RGB Ambient Lighting, Qi 15W Wireless Phone Charger, Touch Slider Control', 'Elevate your workspace aesthetics with AuraGlow. Offers stepless dimming, 5 color temperature presets, built-in wireless charging pad, and eye-care anti-blue light filter.', 'Power Input: USB-C 30W
Wireless Charger Output: 15W Fast Charge
Color Temperature: 2700K - 6500K
Luminous Flux: 800 Lumens', 3499.00, 20.00, 35, 4.7, 11, 0, 1, 1),
(7, 5, 'UrbanShield Waterproof Backpack', 'urbanshield-waterproof-backpack', 'Anti-theft TSA Lock, Built-in USB Charging Port, Fits up to 16" Laptops', 'Designed for daily commuters and global travelers. Crafted from high-density water-repellent oxford fabric with breathable padded shoulder straps and hidden lumbar security pocket.', 'Capacity: 28 Liters
Material: 900D Oxford Water-Resistant Polyester
Laptop Compartment: Up to 16-inch Dedicated Padded Sleeve
Security: Hidden Back Pocket + Combination Lock', 2999.00, 35.00, 50, 4.8, 31, 1, 0, 1),
(8, 1, 'VisionStream 4K Webcam', 'visionstream-4k-webcam', '4K UHD Resolution @ 30FPS, Dual Noise Reduction Mics, Auto Focus & Privacy Shutter', 'Look and sound professional in every online meeting, stream, or class. Dual stereo microphones block out ambient background noise while AI auto-framing keeps you centered.', 'Resolution: 4K 3840x2160 @ 30fps / 1080p @ 60fps
Sensor: 1/2.8" Sony CMOS
Field of View: 90 Degrees Wide Angle
Connection: USB Plug and Play', 5999.00, 18.00, 30, 4.6, 17, 0, 0, 1);

-- Product Images
INSERT OR IGNORE INTO product_images (id, product_id, image_url, is_primary) VALUES
(1, 1, 'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=800&q=80', 1),
(2, 1, 'https://images.unsplash.com/photo-1611186871348-b1ce696e52c9?w=800&q=80', 0),
(3, 2, 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&q=80', 1),
(4, 2, 'https://images.unsplash.com/photo-1484704849700-f032a568e944?w=800&q=80', 0),
(5, 3, 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=800&q=80', 1),
(6, 3, 'https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?w=800&q=80', 0),
(7, 4, 'https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=800&q=80', 1),
(8, 5, 'https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=800&q=80', 1),
(9, 6, 'https://images.unsplash.com/photo-1534073828943-f801091bb18c?w=800&q=80', 1),
(10, 7, 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=800&q=80', 1),
(11, 8, 'https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=800&q=80', 1);
