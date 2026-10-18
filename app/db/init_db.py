from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import Base, engine
from app.models.user import User, UserRole
from app.models.site_content import SiteContent
from app.models.reservation import Table
from app.models.menu import Category, MenuItem
from app.models.navigation import NavItem
from app.models.branch import Branch
from app.models.banner_slide import BannerSlide
from app.models.story import Story
from app.models.dynamic_page import DynamicPage
from app.core.security import get_password_hash


async def init_database():
    """Create tables and seed initial default records if not present."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def seed_initial_data(session: AsyncSession):
    # 1. Seed Admin & Demo Customer
    admin_result = await session.execute(select(User).where(User.email == "admin@restaurant.com"))
    if not admin_result.scalar_one_or_none():
        admin_user = User(
            name="Restaurant Admin",
            email="admin@restaurant.com",
            hashed_password=get_password_hash("admin123"),
            role=UserRole.ADMIN,
            is_active=True,
        )
        session.add(admin_user)

    customer_result = await session.execute(select(User).where(User.email == "customer@example.com"))
    if not customer_result.scalar_one_or_none():
        customer_user = User(
            name="Jane Doe",
            email="customer@example.com",
            hashed_password=get_password_hash("customer123"),
            role=UserRole.CUSTOMER,
            is_active=True,
        )
        session.add(customer_user)

    # 2. Seed Dynamic Site Content (CMS) with Footer & Theme Colors
    default_cms = {
        "site_name": ("Aura Gourmet & Bistro", "branding", "Brand Name"),
        "hero_title": ("GOODNESS EATS", "hero", "Main Hero Headline"),
        "hero_subtitle": ("Experience an unforgettable dining journey crafted with farm-to-table ingredients, authentic woodfired flavors, and world-class culinary finesse.", "hero", "Hero Subtext"),
        "announcement_banner": ("Grand Opening: Reserve now & receive complimentary signature dessert!", "banner", "Top Header Banner"),
        "operating_hours": ("Mon - Sun: 11:30 AM – 11:00 PM", "hours", "Standard Operating Hours"),
        "contact_phone": ("+1 (555) 789-2341", "contact", "Restaurant Contact Number"),
        "contact_email": ("reservations@aurabistro.com", "contact", "Booking Inquiries Email"),
        "address": ("452 Epicurean Avenue, Silicon District, CA 94016", "contact", "Physical Address"),
        "logo_text": ("AURA", "branding", "Navbar Brand Logo Text"),
        "brand_logo_url": ("", "branding", "Custom Uploaded Brand Logo URL"),
        "currency_symbol": ("$", "general", "Display Currency Symbol"),
        # Footer CMS
        "footer_about_text": ("An epicurean sanctuary celebrating gastronomic brilliance, woodfired mastery, and farm-to-table integrity.", "footer", "Footer About Text"),
        "footer_copyright": ("© 2026 Aura Bistro & Bar. All rights reserved.", "footer", "Footer Copyright Notice"),
        "footer_bg_color": ("#133820", "footer", "Footer Background Color Hex"),
        "footer_dining_notice": ("Kitchen closes 45 minutes prior to standard closing time.", "footer", "Kitchen Closing Notice"),
        "social_instagram": ("https://instagram.com/aurabistro", "social", "Instagram Profile URL"),
        "social_facebook": ("https://facebook.com/aurabistro", "social", "Facebook Profile URL"),
        "social_twitter": ("https://twitter.com/aurabistro", "social", "Twitter / X Profile URL"),
        "social_youtube": ("https://youtube.com/@aurabistro", "social", "YouTube Channel URL"),
        # Theme Customization
        "theme_primary_color": ("#133820", "theme", "Primary Brand Color"),
        "theme_accent_color": ("#d97706", "theme", "Accent Highlight Color"),
    }

    for key, (val, cat, desc) in default_cms.items():
        existing = await session.execute(select(SiteContent).where(SiteContent.key == key))
        if not existing.scalar_one_or_none():
            session.add(SiteContent(key=key, value=val, category=cat, description=desc))

    # 3. Seed Restaurant Dining Tables
    tables_result = await session.execute(select(Table))
    if not tables_result.scalars().first():
        sample_tables = [
            Table(table_number="T1", capacity=2, location="window"),
            Table(table_number="T2", capacity=2, location="indoor"),
            Table(table_number="T3", capacity=4, location="indoor"),
            Table(table_number="T4", capacity=4, location="patio"),
            Table(table_number="T5", capacity=6, location="outdoor"),
            Table(table_number="T6", capacity=8, location="indoor"),
        ]
        session.add_all(sample_tables)

    # 4. Seed Categories and Signature Menu Items
    cat_result = await session.execute(select(Category))
    if not cat_result.scalars().first():
        cat_starters = Category(name="Starters & Appetizers", slug="starters", display_order=1)
        cat_mains = Category(name="Artisan Mains", slug="mains", display_order=2)
        cat_desserts = Category(name="Desserts & Patisserie", slug="desserts", display_order=3)
        cat_drinks = Category(name="Signature Cocktails", slug="drinks", display_order=4)
        session.add_all([cat_starters, cat_mains, cat_desserts, cat_drinks])
        await session.flush()

        sample_items = [
            MenuItem(
                category_id=cat_starters.id,
                name="Truffle Wild Mushroom Arancini",
                description="Crispy arborio rice spheres infused with black summer truffle, fontina melt, and garlic aioli.",
                price=16.00,
                photo_url="https://images.unsplash.com/photo-1541529086526-db283c563270?auto=format&fit=crop&w=800&q=80",
                tags="Chef Special,Vegetarian",
                in_stock=True,
                is_top_recipe=True,
                is_chef_special=True,
            ),
            MenuItem(
                category_id=cat_starters.id,
                name="Charred Octopus Carpaccio",
                description="Tender citrus-cured Spanish octopus with smoked paprika emulsion, caper berries, and micro greens.",
                price=21.50,
                photo_url="https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=800&q=80",
                tags="Seafood,Gluten-Free",
                in_stock=True,
                is_top_recipe=False,
                is_chef_special=True,
            ),
            MenuItem(
                category_id=cat_mains.id,
                name="Dry-Aged Wagyu Ribeye (10oz)",
                description="Prime cut grilled over binchotan charcoal, accompanied by roasted bone marrow butter and potato mousseline.",
                price=58.00,
                photo_url="https://images.unsplash.com/photo-1558030006-450675393462?auto=format&fit=crop&w=800&q=80",
                tags="Top Recipe,Chef Special",
                in_stock=True,
                is_top_recipe=True,
                is_chef_special=True,
            ),
            MenuItem(
                category_id=cat_mains.id,
                name="Pan-Seared Chilean Sea Bass",
                description="Glazed with white miso and ginger dashi broth, served atop wild baby bok choy and lotus root.",
                price=44.00,
                photo_url="https://images.unsplash.com/photo-1519708227418-c8fd9a32b7a2?auto=format&fit=crop&w=800&q=80",
                tags="Seafood,Signature",
                in_stock=True,
                is_top_recipe=True,
                is_chef_special=False,
            ),
            MenuItem(
                category_id=cat_desserts.id,
                name="Valrhona Dark Chocolate Sphere",
                description="Warm salted caramel poured tableside over a chocolate sphere encasing hazelnut praline crunch.",
                price=14.00,
                photo_url="https://images.unsplash.com/photo-1579372786545-d24232daf58c?auto=format&fit=crop&w=800&q=80",
                tags="Chef Special,Sweet",
                in_stock=True,
                is_top_recipe=True,
                is_chef_special=True,
            ),
            MenuItem(
                category_id=cat_drinks.id,
                name="Smoked Rosemary Bourbon Old Fashioned",
                description="Small-batch bourbon, demerara syrup, Angostura bitters, enveloped in aromatic applewood smoke.",
                price=17.00,
                photo_url="https://images.unsplash.com/photo-1514362545857-3bc16c4c7d1b?auto=format&fit=crop&w=800&q=80",
                tags="Signature Drink",
                in_stock=True,
                is_top_recipe=False,
                is_chef_special=True,
            ),
        ]
        session.add_all(sample_items)

    # 5. Seed Dynamic Header Navigation Items (CRUD ready)
    nav_result = await session.execute(select(NavItem))
    if not nav_result.scalars().first():
        default_nav = [
            NavItem(label="Home", route="/", display_order=1, is_active=True),
            NavItem(label="Menu & Bowls", route="/menu", display_order=2, is_active=True),
            NavItem(label="Store Locations", route="/locations", display_order=3, is_active=True),
            NavItem(label="Reservations", route="/reserve", display_order=4, is_active=True),
            NavItem(label="Our Stories", route="/stories", display_order=5, is_active=True),
            NavItem(label="Reviews", route="/reviews", display_order=6, is_active=True),
        ]
        session.add_all(default_nav)

    # 6. Seed Multi-Branch Store Locator Locations
    branch_result = await session.execute(select(Branch))
    if not branch_result.scalars().first():
        default_branches = [
            Branch(
                name="Silicon Valley Flagship",
                city="San Francisco",
                address="452 Epicurean Avenue, Silicon District, CA 94016",
                phone="+1 (555) 789-2341",
                email="sf@aurabistro.com",
                latitude=37.7749,
                longitude=-122.4194,
                opening_hours="Mon - Sun: 11:30 AM – 11:00 PM",
                image_url="https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=800&q=80",
                is_active=True
            ),
            Branch(
                name="Beverly Hills Hearth",
                city="Los Angeles",
                address="9400 Wilshire Boulevard, Beverly Hills, CA 90212",
                phone="+1 (310) 555-8833",
                email="la@aurabistro.com",
                latitude=34.0674,
                longitude=-118.3977,
                opening_hours="Tue - Sun: 12:00 PM – 11:30 PM",
                image_url="https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=800&q=80",
                is_active=True
            ),
            Branch(
                name="SoHo Artisan Kitchen",
                city="New York",
                address="128 Prince Street, SoHo, NY 10012",
                phone="+1 (212) 555-4921",
                email="ny@aurabistro.com",
                latitude=40.7259,
                longitude=-74.0003,
                opening_hours="Mon - Sun: 11:00 AM – 11:00 PM",
                image_url="https://images.unsplash.com/photo-1550966871-3ed3cdb5ed0c?auto=format&fit=crop&w=800&q=80",
                is_active=True
            ),
            Branch(
                name="West Loop Greenery",
                city="Chicago",
                address="800 West Randolph Street, Chicago, IL 60607",
                phone="+1 (312) 555-7766",
                email="chicago@aurabistro.com",
                latitude=41.8845,
                longitude=-87.6477,
                opening_hours="Wed - Sun: 11:30 AM – 10:30 PM",
                image_url="https://images.unsplash.com/photo-1537047902294-62a40c20a6ae?auto=format&fit=crop&w=800&q=80",
                is_active=True
            ),
        ]
        session.add_all(default_branches)

    # 7. Seed Hero Banner Slides
    slide_result = await session.execute(select(BannerSlide))
    if not slide_result.scalars().first():
        default_slides = [
            BannerSlide(
                badge_text="EST. 2026 • SCRATCH KITCHEN",
                script_text="Honest to",
                title="GOODNESS EATS",
                subtitle="Experience an unforgettable dining journey crafted with farm-to-table ingredients, authentic woodfired flavors, and world-class culinary finesse.",
                ribbon_text="ARTISAN GASTRONOMY",
                image_url="/hero_table_banner.jpg",
                button_primary_text="Make a Reservation",
                button_primary_link="/reserve",
                button_secondary_text="Explore Menu & Recipes",
                button_secondary_link="/menu",
                display_order=1,
                is_active=True
            ),
            BannerSlide(
                badge_text="LOCAL HARVEST • DIRECT FARMS",
                script_text="Farm fresh",
                title="SEASONAL BOWLS",
                subtitle="Crisp heirloom greens, warm sprouted farro, charred avocado, and house-whipped green goddess dressing.",
                ribbon_text="ORGANIC HARVEST",
                image_url="https://images.unsplash.com/photo-1540420773420-3366772f4999?auto=format&fit=crop&w=2000&q=85",
                button_primary_text="Taste the Harvest",
                button_primary_link="/menu",
                button_secondary_text="Find Nearest Branch",
                button_secondary_link="/locations",
                display_order=2,
                is_active=True
            ),
            BannerSlide(
                badge_text="WOODFIRED HEARTH",
                script_text="Grilled over binchotan",
                title="HEARTH & FLAME",
                subtitle="Dry-aged prime cuts, blistered sourdough flatbreads, and cultured compound butters crafted with uncompromising care.",
                ribbon_text="LIVE FIRE COOKING",
                image_url="https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=2000&q=85",
                button_primary_text="Reserve Hearth Seating",
                button_primary_link="/reserve",
                button_secondary_text="View Specialties",
                button_secondary_link="/menu",
                display_order=3,
                is_active=True
            ),
        ]
        session.add_all(default_slides)

    # 8. Seed "Our Stories" Blog Engine Articles
    story_result = await session.execute(select(Story))
    if not story_result.scalars().first():
        default_stories = [
            Story(
                title="The Art of Woodfired Sourdough & Hearth Cooking",
                slug="art-of-woodfired-sourdough",
                category="Culinary Craft",
                excerpt="How ancient fermentations, stone-milled heirloom grains, and burning applewood create pure culinary magic.",
                content="<p>Every loaf of bread and woodfired flatbread at Aura begins 48 hours prior to service. We mill organic heirloom grains in-house, marrying them with a heritage levain starter nurtured for over seven years.</p><h3>The Dance of Heat and Smoke</h3><p>Our custom brick hearth burns aged Californian applewood at 750°F, blistering the dough while preserving an airy, moist interior bursting with umami and caramel notes.</p><p>Paired with our cultured sea-salt butter, it is an ode to the fundamental beauty of simplicity.</p>",
                cover_image="https://images.unsplash.com/photo-1509440159596-0249088772ff?auto=format&fit=crop&w=1200&q=80",
                author="Head Baker Marco Santos",
                read_time="3 min read",
                is_published=True
            ),
            Story(
                title="Meet Our Farmers: Regenerative Agriculture at Green Pastures",
                slug="meet-our-farmers-regenerative-agriculture",
                category="Farming Partners",
                excerpt="Behind every bowl is a farmer who cares deeply about living soil, biodiversity, and zero chemicals.",
                content="<p>Great cooking cannot happen without great agriculture. For four years, Aura has partnered directly with Green Pastures Farm in the Salinas Valley.</p><h3>Living Soils Build Unmatched Flavor</h3><p>By rotating cover crops and eliminating synthetic sprays, the earth teems with microbiome vitality. When a carrot is pulled from living soil, the natural sweetness and mineral complexity need no mask.</p><p>We are proud to serve produce harvested under 24 hours from earth to table.</p>",
                cover_image="https://images.unsplash.com/photo-1595974482597-4b8da8879bc5?auto=format&fit=crop&w=1200&q=80",
                author="Elena Rostova (Head of Sourcing)",
                read_time="5 min read",
                is_published=True
            ),
            Story(
                title="Zero Seed Oils: Why We Cook Exclusively with Cold-Pressed Olive Oil & Grass-Fed Tallow",
                slug="zero-seed-oils-our-commitment",
                category="Food Philosophy",
                excerpt="Our uncompromising commitment to real ingredients that honor human biology and planetary health.",
                content="<p>In an age where industrial seed oils dominate commercial kitchens, we made a radical decision: zero canola, soybean, corn, or sunflower oils anywhere on our premises.</p><h3>Pure Fats, Pure Taste</h3><p>We cook solely with cold-pressed single-estate Koroneiki extra virgin olive oil, grass-fed organic beef tallow, and pasture-raised butter. The outcome is clean, crisp flavors that leave you feeling energized and nourished.</p>",
                cover_image="https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?auto=format&fit=crop&w=1200&q=80",
                author="Executive Chef David Chen",
                read_time="4 min read",
                is_published=True
            ),
        ]
        session.add_all(default_stories)

    await session.commit()
