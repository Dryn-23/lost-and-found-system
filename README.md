# Lost Today, Found Someday
### A School-Based Lost and Found Management System

A desktop lost-and-found catalog built with **Python, Tkinter/ttk, and SQLite**. Public visitors can browse/search and submit a claim without registering or signing in. Only the Admin Office can enter found items, review private finder/claim information, approve or reject claims, and record physical returns.

## Run the project

1. Install Python 3.10 or newer.
2. Make sure Tkinter is installed. It is included with most Windows/macOS Python installations. On Debian/Ubuntu, install it with:
   ```bash
   sudo apt install python3-tk
   ```
3. Open a terminal in this project directory and run:
   ```bash
   python main.py
   ```

No pip packages are required. On first launch the application creates `database/lost_found.db`, creates its tables, adds a demonstration Admin, and seeds fictional sample items if the catalog is empty. The database file is local to this project and is intentionally not included in the source archive.

## Demo Admin account

```text
Username: admin
Password: admin123
```

This is a classroom/demo credential. Do not use it for a real school deployment. Admin passwords are stored as salted PBKDF2-HMAC-SHA256 hashes, not as plaintext. A real deployment should provide a password-change / credential-rotation process, restrict access to the computer and database file, and follow the school's data-retention and privacy policies.

## Public and Admin workflows

### Public visitor — no account

1. The application opens directly to the public catalog.
2. Browse, search by item name/category/color/brand/location, and filter by category, location, date found, and status.
3. Open safe item details and submit a Student, Teacher, or School Utility Personnel claim.
4. Receive a `CLAIM-YYYY-00000` reference. The claim is **not** automatically approved.
5. Bring the Claim ID and official school identification to the Admin Office for in-person verification.

There is no public login or registration, and visitors cannot add found items.

### Admin Office

1. Use the small **Admin** link in the public-page footer and sign in.
2. Receive and physically secure the item. Interview the finder and complete the **Add Found Item** form. The form requires confirmation that the item was surrendered to the Admin Office.
3. Review incoming claims and compare the claimant's school ID and answers with the physical item.
4. Request further in-person verification, approve, or reject the claim. Approval alone does not set the item to Returned.
5. After physically handing over an approved item, use **Mark as Returned** and record the return date, time, releasing Admin, claimant, and notes.

## Privacy and safety

- Public SQL queries use an explicit allow-list of catalog-safe item fields. Finder names, finder IDs/contacts, private notes, and storage locations are not returned to the public views.
- Claimant identity and answers are only displayed in the authenticated Admin workspace.
- Public descriptions should remain general. Do not publish serial numbers, wallet contents, private marks, or identifying details that make fraudulent claims easier.
- Review any optional item photo before adding it; a photo can reveal details even when text fields are safe.
- SQLite is a local database and is **not encrypted at rest**. Protect the device/file with operating-system access controls and do not use real student data in an unsecured demo.
- The included sample finders and items are clearly marked fictional demo data.

## Project structure

```text
school_lost_found/
├── main.py
├── README.md
├── requirements.txt
├── database/
│   ├── __init__.py
│   └── database.py       # SQLite schema, queries, transactions, demo seed
├── models/
│   ├── __init__.py
│   ├── user.py           # User and unauthenticated PublicUser
│   ├── admin.py          # Admin identity and password hashing
│   ├── person.py         # Abstract SchoolPerson + Student/Teacher/UtilityStaff
│   ├── finder.py         # Finder interview composition model
│   ├── item.py           # Item model and public-field boundary
│   └── claim.py          # Claim model and claim statuses
├── controllers/
│   ├── __init__.py
│   ├── system_controller.py
│   ├── admin_controller.py
│   ├── item_controller.py
│   └── claim_controller.py
├── views/
│   ├── __init__.py
│   ├── app.py            # Tk window and top-level navigation
│   ├── ui.py             # ttk theme, scrollable frame, tree helpers
│   ├── public_views.py   # Catalog, item details, public claim form
│   ├── admin_login.py
│   ├── admin_views.py    # Dashboard, items, intake, claims, reports, logs
│   └── admin_dialogs.py  # Private detail/review/return dialogs
├── utils/
│   ├── __init__.py
│   ├── validators.py
│   └── helpers.py
└── tests/
    └── test_workflows.py
```

`database/lost_found.db` is generated on first run and is ignored by version control.

## OOP design notes

- **Abstraction:** `SchoolPerson` is an abstract base class defining the common person interface.
- **Inheritance:** `Student`, `Teacher`, and `UtilityStaff` specialize `SchoolPerson`; these are claim/finder identity types, not application accounts.
- **Polymorphism:** each school-person subclass implements its role and affiliation, and `to_record()` yields a consistent database shape used by the intake and claim workflows.
- **Encapsulation:** identity fields are exposed through read-only properties; controllers validate and coordinate state changes before the database manager writes them.
- **Composition:** a `Finder` contains a `SchoolPerson` plus interview answers. `Claim` contains its claimant and ownership answers. `LostFoundSystem` composes the database and focused controllers.
- **Separation of concerns:** `models/` contains domain data, `controllers/` implements application rules, `database/` owns persistence, and `views/` contains Tkinter UI.

## Database tables

The database manager creates `admins`, `finders`, `items`, `claims`, `claim_verifications`, `returns`, and `activity_logs`, with foreign keys and indexes. Claim submission and item/finder intake are transactional. Search values use parameterized SQL. Item history is archived rather than permanently deleted.

## Tests

Run the database workflow tests (no display server is needed):

```bash
python -m unittest discover -s tests -v
```

The tests use a temporary SQLite database and cover demo seeding, public/private field separation, duplicate claim prevention, Admin decisions, and the physical-return transition.
