"""Database migration and seeding script for the ChemStore Pro warehouse.

Applies incremental column migrations to existing tables, creates the tables
used by newer features (bids, product questions/answers), and populates a
realistic marketplace catalog with reviews, bids, and Q&A data when the
database is empty or when FORCE_SEED=1 is set.
"""
import sqlite3
from datetime import datetime, timedelta

def migrate_and_seed():
    # Open (or create) the SQLite database and get a cursor for execution.
    conn = sqlite3.connect('warehouse.db')
    cursor = conn.cursor()

    # Column migrations on items
    # Each ALTER is attempted individually; errors mean the column exists already.
    item_cols = [
        "ALTER TABLE items ADD COLUMN description TEXT DEFAULT ''",
        "ALTER TABLE items ADD COLUMN image_url TEXT DEFAULT ''",
        "ALTER TABLE items ADD COLUMN active INTEGER NOT NULL DEFAULT 1",
        "ALTER TABLE items ADD COLUMN featured INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE items ADD COLUMN seller_id INTEGER DEFAULT 1",
        "ALTER TABLE items ADD COLUMN seller_name TEXT DEFAULT 'ChemStore Official'",
        "ALTER TABLE items ADD COLUMN condition TEXT DEFAULT 'Brand New'",
        "ALTER TABLE items ADD COLUMN listing_type TEXT DEFAULT 'fixed'",
        "ALTER TABLE items ADD COLUMN starting_bid REAL DEFAULT 0.0",
        "ALTER TABLE items ADD COLUMN current_bid REAL DEFAULT 0.0",
        "ALTER TABLE items ADD COLUMN bid_count INTEGER DEFAULT 0",
        "ALTER TABLE items ADD COLUMN auction_end TEXT DEFAULT ''",
        "ALTER TABLE items ADD COLUMN brand TEXT DEFAULT ''",
        "ALTER TABLE items ADD COLUMN badge TEXT DEFAULT ''",
    ]
    for col in item_cols:
        try:
            cursor.execute(col)
        except sqlite3.OperationalError:
            pass

    # Column migrations on orders
    order_cols = [
        "ALTER TABLE orders ADD COLUMN discount_cents INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE orders ADD COLUMN coupon_code TEXT",
        "ALTER TABLE orders ADD COLUMN payment_method TEXT DEFAULT 'cod'",
        "ALTER TABLE orders ADD COLUMN carrier TEXT DEFAULT 'Pakistan Post'",
        "ALTER TABLE orders ADD COLUMN tracking_number TEXT DEFAULT ''",
        "ALTER TABLE orders ADD COLUMN estimated_delivery TEXT DEFAULT ''",
    ]
    for col in order_cols:
        try:
            cursor.execute(col)
        except sqlite3.OperationalError:
            pass

    # Column migrations on users
    user_cols = [
        'ALTER TABLE users ADD COLUMN profile_pic TEXT DEFAULT "default.png"',
        'ALTER TABLE users ADD COLUMN approved INTEGER DEFAULT 1',
        'ALTER TABLE users ADD COLUMN is_seller INTEGER DEFAULT 0',
        'ALTER TABLE users ADD COLUMN seller_name TEXT DEFAULT ""',
        'ALTER TABLE users ADD COLUMN seller_rating REAL DEFAULT 5.0',
        'ALTER TABLE users ADD COLUMN seller_sales_count INTEGER DEFAULT 0',
    ]
    for col in user_cols:
        try:
            cursor.execute(col)
        except sqlite3.OperationalError:
            pass

    # Tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bids (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            bidder_name TEXT NOT NULL,
            amount REAL NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (item_id) REFERENCES items (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS product_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            question TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (item_id) REFERENCES items (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS product_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            answer TEXT NOT NULL,
            is_seller INTEGER NOT NULL DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (question_id) REFERENCES product_questions (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.commit()

    # Now populate rich marketplace products
    # First, let's delete existing dummy row if only 1 item with price 0
    count = cursor.execute('SELECT COUNT(*) FROM items').fetchone()[0]
    import os
    if count <= 1 or os.environ.get('FORCE_SEED') == '1':
        cursor.execute('DELETE FROM items')
        cursor.execute('DELETE FROM reviews')
        cursor.execute('DELETE FROM bids')
        cursor.execute('DELETE FROM product_questions')
        cursor.execute('DELETE FROM product_answers')
        try:
            cursor.execute("UPDATE sqlite_sequence SET seq = 0 WHERE name = 'items'")
        except sqlite3.OperationalError:
            pass
        conn.commit()

        now = datetime.now()
        catalog = [
            (
                'CHEM-001', 'Acetone Technical Grade 99.5%', 'Solvents', 280, 'L', 24.99,
                'Industrial and laboratory grade acetone for precision degreasing, solvent cleaning, resin thinning, and analytical prep. Fast evaporating formula with zero oily residues.',
                '/static/images/acetone.svg', 1, 1, 1, 'Apex Chemical Supply', 'Brand New', 'fixed',
                0.0, 0.0, 0, '', 'PureChem Labs', 'Best Seller'
            ),
            (
                'CHEM-002', 'Ethanol Denatured 99% ACS Reagent Grade', 'Solvents', 190, 'L', 38.50,
                'High-purity ACS Reagent Grade ethanol, specifically denatured for laboratory sanitization, histology, specimen preservation, and organic synthesis.',
                '/static/images/ethanol.svg', 1, 1, 1, 'Nova Scientific Labs', 'Brand New', 'fixed',
                0.0, 0.0, 0, '', 'Apex Reagents', 'ChemStore\'s Choice'
            ),
            (
                'CHEM-003', 'High Purity Isopropyl Alcohol 99.9% (Surplus Lot)', 'Solvents', 420, 'L', 29.99,
                'Ultra-pure USP anhydrous isopropanol in 1-gallon sealed containers. Excellent for electronics cleaning, optics, pharmaceutical manufacturing, and sterilization.',
                '/static/images/isopropyl.svg', 1, 1, 1, 'Direct Surplus Direct', 'Brand New', 'both',
                18.00, 23.50, 7, (now + timedelta(days=2, hours=4)).isoformat(), 'PureChem Labs', 'Ending Soon'
            ),
            (
                'CHEM-004', 'Hydrochloric Acid 37% Concentrated Reagent', 'Acids & Bases', 140, 'L', 42.00,
                'ACS Grade 37% fuming muriatic acid for titrations, pH adjustments, metallurgical etching, and chemical syntheses. Packaged in acid-resistant safety bottles.',
                '/static/images/hydrochloric.svg', 1, 1, 1, 'ChemStore Official', 'Brand New', 'fixed',
                0.0, 0.0, 0, '', 'SigmaGrade', 'Best Seller'
            ),
            (
                'CHEM-005', 'Sulfuric Acid 98% Concentrated Heavy Grade', 'Acids & Bases', 95, 'L', 54.95,
                'Laboratory grade concentrated sulfuric acid for analytical digestions, battery manufacturing, desiccation, and chemical processing. Handle with care.',
                '/static/images/sulfuric.svg', 1, 0, 1, 'ChemStore Official', 'Brand New', 'fixed',
                0.0, 0.0, 0, '', 'SigmaGrade', ''
            ),
            (
                'CHEM-006', 'Sodium Hydroxide Pellets 99% Pure Caustic Soda', 'Acids & Bases', 320, 'kg', 19.95,
                'Technical grade anhydrous caustic soda pellets. Ideal for alkaline saponification, biodigestion, drain clearing, and neutralization reactions.',
                '/static/images/sodium_hydroxide.svg', 1, 1, 1, 'Apex Chemical Supply', 'Brand New', 'fixed',
                0.0, 0.0, 0, '', 'LabSupply Direct', 'Best Seller'
            ),
            (
                'LAB-101', 'Borosilicate 3.3 Glass Beaker Set (5 Pieces: 50-1000 mL)', 'Laboratory Glassware', 85, 'set', 34.50,
                'Professional Griffin low-form glass beakers with heavy uniform wall thickness, pour spouts, and double-scale graduations. Thermal shock resistant up to 500°C.',
                '/static/images/beakers.svg', 1, 1, 1, 'Nova Scientific Labs', 'Brand New', 'fixed',
                0.0, 0.0, 0, '', 'PyrexTech Labs', 'Best Seller'
            ),
            (
                'LAB-102', 'Erlenmeyer Flask Heavy-Duty 1000 mL Narrow Neck', 'Laboratory Glassware', 110, 'pcs', 18.99,
                'Heavy-duty conical titration flask made of high-expansion borosilicate glass. Reinforced beaded rim prevents chipping during intensive laboratory swirling.',
                '/static/images/erlenmeyer.svg', 1, 0, 1, 'Nova Scientific Labs', 'Brand New', 'both',
                12.00, 15.50, 4, (now + timedelta(days=1, hours=8)).isoformat(), 'PyrexTech Labs', ''
            ),
            (
                'LAB-103', 'Liebig Reflux Glass Condenser 300mm 24/40 Joint', 'Laboratory Glassware', 35, 'pcs', 45.00,
                'Precision ground 24/40 standard taper joints with hose barbs for distillation and fractional reflux setups. Pristine optical clarity and airtight sealing.',
                '/static/images/condenser.svg', 1, 1, 1, 'Direct Surplus Direct', 'Refurbished', 'auction',
                22.00, 31.00, 11, (now + timedelta(days=2, hours=18)).isoformat(), 'SynthGlass Pro', 'Ending Soon'
            ),
            (
                'INST-201', 'Digital Precision Analytical Balance 0.001g (1mg High Accuracy)', 'Precision Instruments', 40, 'unit', 149.00,
                'Electromagnetic force restoration laboratory scale with windshield draft chamber, LCD backlit display, gram/ounce/carat conversion, and dynamic calibration.',
                '/static/images/scale.svg', 1, 1, 1, 'Ohaus Precision Store', 'Brand New', 'fixed',
                0.0, 0.0, 0, '', 'Ohaus Precision', 'ChemStore\'s Choice'
            ),
            (
                'INST-202', 'Digital Laboratory pH Meter with ATC Auto-Calibration', 'Precision Instruments', 65, 'unit', 44.95,
                'Handheld high-accuracy digital pH pen with automatic temperature compensation (ATC) and 3-point calibration buffer packet included.',
                '/static/images/ph_meter.svg', 1, 1, 1, 'Nova Scientific Labs', 'Brand New', 'fixed',
                0.0, 0.0, 0, '', 'HannaTech', 'Top Rated'
            ),
            (
                'INST-203', 'Antique Vintage Brass Laboratory Balance with Weight Box (1950s)', 'Precision Instruments', 1, 'set', 120.00,
                'Vintage laboratory collectible! Solid brass double-pan analytical scale mounted on mahogany base with leveling screws and complete brass gram weight kit.',
                '/static/images/vintage_scale.svg', 1, 1, 1, 'Cambridge Vintage Labs', 'Used - Good', 'auction',
                50.00, 78.00, 19, (now + timedelta(days=3, hours=12)).isoformat(), 'Cambridge Scientific', 'Ending Soon'
            ),
            (
                'SAFE-301', 'Heavy-Duty Nitrile Chemical Gloves (Box of 100, Powder-Free)', 'Safety & Protection', 240, 'pack', 16.99,
                'Textured fingertips for superior wet/dry grip, 6-mil puncture-resistant nitrile material with barrier resistance to acids, bases, solvents, and biologicals.',
                '/static/images/gloves.svg', 1, 1, 1, 'ChemStore Official', 'Brand New', 'fixed',
                0.0, 0.0, 0, '', 'SafeShield Pro', 'Best Seller'
            ),
            (
                'SAFE-302', 'Full-Face Organic Vapor Respirator Mask with Filter Set', 'Safety & Protection', 55, 'unit', 59.95,
                'Anti-fog panoramic wide-angle polycarbonate shield with dual activated charcoal cartridges for acid gases, organic vapors, and particulates.',
                '/static/images/respirator.svg', 1, 1, 1, 'Apex Chemical Supply', 'Brand New', 'fixed',
                0.0, 0.0, 0, '', '3M Safety', 'ChemStore\'s Choice'
            ),
            (
                'SAFE-303', 'Anti-Fog Impact Chemical Splash Goggles with Indirect Vents', 'Safety & Protection', 180, 'pcs', 12.50,
                'Soft elastomer seal conforms to facial contours, clear UV-coated scratch-resistant lens, with four indirect vent caps to prevent chemical ingress.',
                '/static/images/goggles.svg', 1, 0, 1, 'Apex Chemical Supply', 'Brand New', 'fixed',
                0.0, 0.0, 0, '', 'SafeShield Pro', ''
            ),
            (
                'CHEM-007', 'Copper(II) Sulfate Pentahydrate Crystals 99% Reagent', 'Reagents', 125, 'kg', 21.50,
                'Vibrant royal blue copper sulfate crystals for electroplating, Fehling solution reagent, algaecide treatment, and educational chemistry demonstrations.',
                '/static/images/copper_sulfate.svg', 1, 1, 1, 'ChemStore Official', 'Brand New', 'fixed',
                0.0, 0.0, 0, '', 'CrystalChem', 'Top Rated'
            ),
            (
                'INST-204', 'Digital Magnetic Stirrer with Ceramic Hot Plate (2000 RPM)', 'Precision Instruments', 28, 'unit', 89.00,
                'Laboratory grade heating plate with magnetic drive up to 2000 RPM and 380°C hotplate temperature. Includes Teflon magnetic stir bar and support stand.',
                '/static/images/stirrer.svg', 1, 1, 1, 'Nova Scientific Labs', 'Refurbished', 'both',
                45.00, 62.00, 8, (now + timedelta(days=2, hours=10)).isoformat(), 'LabStir Ultra', 'Ending Soon'
            ),
            (
                'LAB-104', 'Heavy Cast Iron Retort Support Stand with 2 Ring Clamps', 'Laboratory Glassware', 45, 'set', 28.50,
                'Corrosion-resistant baked enamel cast iron base (8x5 inch) with 24-inch chrome-plated steel rod, burette clamp, and two boss head rings.',
                '/static/images/retort_stand.svg', 1, 0, 1, 'ChemStore Official', 'Brand New', 'auction',
                15.00, 22.00, 6, (now + timedelta(days=1, hours=22)).isoformat(), 'LabCraft', ''
            )
        ]

        for item in catalog:
            cursor.execute('''
                INSERT INTO items (
                    code, name, category, quantity, unit, price, description, image_url,
                    active, featured, seller_id, seller_name, condition, listing_type,
                    starting_bid, current_bid, bid_count, auction_end, brand, badge
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', item)
        conn.commit()

        # Seed realistic reviews
        sample_reviews = [
            (1, 1, 5, 'Super high purity, completely residue free!', 'Used this acetone for degreasing delicate stainless steel parts before vacuum brazing. Evaporated instantly with zero residue. Fast delivery and secure packaging.', 1),
            (1, 1, 4, 'Great solvent, well packaged', 'The bottle arrived safe and sealed with tamper-evident tape. Perfect technical grade quality.', 1),
            (2, 1, 5, 'Perfect for specimen preservation', 'Exactly what our lab needed for histology tissue preparation. Will definitely reorder.', 1),
            (3, 1, 5, 'Best deal on 99.9% IPA anywhere', 'Winning bid on this IPA was an absolute steal. Sealed 1-gallon jug, water-clear and dry.', 1),
            (4, 1, 5, 'High concentration ACS grade', 'Great quality 37% HCl. Titration assays matched the specification sheet perfectly.', 1),
            (7, 1, 5, 'Outstanding borosilicate quality', 'Pyrex-grade thick glass. I heated solutions over a Bunsen burner with no cracking. Beakers fit comfortably inside each other for storage.', 1),
            (10, 1, 5, 'Surprisingly accurate for the price', 'Calibrated with certified test weights and it repeated down to +/-0.001g consistently. The draft shield makes a huge difference in avoiding air current drift.', 1),
            (11, 1, 4, 'Reliable pH meter with quick stabilization', 'Reading stabilizes within 10 seconds. Buffer powders included were very convenient.', 1),
            (13, 1, 5, 'Tough, no tears with solvents', 'These gloves hold up to both acetone and ethanol without degrading or ripping. Good textured grip.', 1),
            (14, 1, 5, 'Comfortable seal and complete vapor block', 'You cannot smell a drop of organic vapors or acid fumes with this on. Crystal clear visor.', 1),
            (17, 1, 5, 'Smooth stir action and rapid heating', 'The ceramic plate heats up evenly and the magnetic vortex is strong and quiet.', 1)
        ]
        for rev in sample_reviews:
            cursor.execute('''
                INSERT INTO reviews (item_id, user_id, rating, title, body, verified, approved)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            ''', rev)

        # Seed sample bids for auction items
        sample_bids = [
            (3, 1, 'chem_tech_99', 19.50, (now - timedelta(hours=14)).strftime('%Y-%m-%d %H:%M:%S')),
            (3, 1, 'lab_buyer_dc', 21.00, (now - timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')),
            (3, 1, 'bio_researcher', 23.50, (now - timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S')),
            (9, 1, 'glass_collector', 24.00, (now - timedelta(hours=18)).strftime('%Y-%m-%d %H:%M:%S')),
            (9, 1, 'synth_chemist', 28.00, (now - timedelta(hours=9)).strftime('%Y-%m-%d %H:%M:%S')),
            (9, 1, 'lab_pro_tx', 31.00, (now - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')),
            (12, 1, 'antique_dr', 55.00, (now - timedelta(hours=22)).strftime('%Y-%m-%d %H:%M:%S')),
            (12, 1, 'boston_collector', 68.00, (now - timedelta(hours=10)).strftime('%Y-%m-%d %H:%M:%S')),
            (12, 1, 'curator_mike', 78.00, (now - timedelta(hours=3)).strftime('%Y-%m-%d %H:%M:%S')),
            (17, 1, 'diy_biologist', 48.00, (now - timedelta(hours=12)).strftime('%Y-%m-%d %H:%M:%S')),
            (17, 1, 'pharm_student', 56.00, (now - timedelta(hours=5)).strftime('%Y-%m-%d %H:%M:%S')),
            (17, 1, 'chem_tech_99', 62.00, (now - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S'))
        ]
        for b in sample_bids:
            cursor.execute('''
                INSERT INTO bids (item_id, user_id, bidder_name, amount, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', b)

        # Seed sample Q&A
        sample_questions = [
            (1, 1, 'Does this technical grade acetone contain any oils or water impurities?'),
            (2, 1, 'What is the denaturant used in this ethanol?'),
            (7, 1, 'Are these beakers microwave and autoclave safe?'),
            (10, 1, 'Does this balance include calibration test weights in the box?'),
            (14, 1, 'Are the replacement filter cartridges standard universal bayonet mount?')
        ]
        for q in sample_questions:
            c = cursor.execute('''
                INSERT INTO product_questions (item_id, user_id, question)
                VALUES (?, ?, ?)
            ''', q)
            qid = c.lastrowid
            # Answers
            answers = {
                1: ('This acetone is 99.5% minimum purity with less than 0.3% moisture and zero non-volatile oily residue. It is tested for rapid dry evaporate test.', 1),
                2: ('This formula is specifically denatured using standard reagent denaturants (isopropanol and methanol blend), suitable for histological and analytical work.', 1),
                3: ('Yes, they are made from genuine Borosilicate 3.3 glass and are fully autoclavable at 121°C and safe for microwave heating.', 1),
                4: ('Yes! It includes a certified 100g calibration weight and tweezers for handling calibration weights.', 1),
                5: ('Yes, the cartridges use the standard twin-bayonet interface compatible with all 6000 and 7000 series replacement filters.', 1)
            }
            if q[0] in answers:
                ans_text, is_seller = answers[q[0]]
                cursor.execute('''
                    INSERT INTO product_answers (question_id, user_id, answer, is_seller)
                    VALUES (?, ?, ?, ?)
                ''', (qid, 1, ans_text, is_seller))

        conn.commit()
        print('Seeded rich marketplace catalog, reviews, bids, and Q&A successfully!')
    else:
        print(f'Database already contains {count} items. Migrations applied.')

    conn.close()

if __name__ == '__main__':
    migrate_and_seed()
