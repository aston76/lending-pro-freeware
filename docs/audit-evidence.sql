-- Reproducible SQLite evidence snapshot for the 1.5.1 application audit.
-- The values below are the reviewed outputs recorded on 2026-08-13.

CREATE TABLE final_test_run (
    release TEXT PRIMARY KEY,
    passed_tests INTEGER NOT NULL
);

INSERT INTO final_test_run VALUES ('1.5.1', 27);

CREATE TABLE dependency_audit (
    release TEXT NOT NULL,
    ecosystem TEXT NOT NULL,
    known_vulnerabilities INTEGER NOT NULL,
    broken_requirements INTEGER NOT NULL
);

INSERT INTO dependency_audit VALUES ('1.5.1', 'npm', 0, 0);
INSERT INTO dependency_audit VALUES ('1.5.1', 'python', 0, 0);

CREATE TABLE browser_view_audit (
    release TEXT NOT NULL,
    view_name TEXT NOT NULL,
    viewport_width INTEGER NOT NULL,
    broken_images INTEGER NOT NULL,
    console_errors INTEGER NOT NULL
);

INSERT INTO browser_view_audit VALUES ('1.5.1', 'Dashboard', 390, 0, 0);
INSERT INTO browser_view_audit VALUES ('1.5.1', 'Clients', 390, 0, 0);
INSERT INTO browser_view_audit VALUES ('1.5.1', 'Loans', 390, 0, 0);
INSERT INTO browser_view_audit VALUES ('1.5.1', 'Payments', 390, 0, 0);
INSERT INTO browser_view_audit VALUES ('1.5.1', 'Collection Calendar', 390, 0, 0);
INSERT INTO browser_view_audit VALUES ('1.5.1', 'Overdue Alerts', 390, 0, 0);
INSERT INTO browser_view_audit VALUES ('1.5.1', 'Referral Commissions', 390, 0, 0);
INSERT INTO browser_view_audit VALUES ('1.5.1', 'Settings', 390, 0, 0);
INSERT INTO browser_view_audit VALUES ('1.5.1', 'Help and User Guide', 390, 0, 0);
INSERT INTO browser_view_audit VALUES ('1.5.1', 'About', 390, 0, 0);
INSERT INTO browser_view_audit VALUES ('1.5.1', 'System Logs', 390, 0, 0);

CREATE TABLE audit_coverage (
    release TEXT NOT NULL,
    area TEXT NOT NULL,
    passed_gates INTEGER NOT NULL,
    scope TEXT NOT NULL
);

INSERT INTO audit_coverage VALUES ('1.5.1', 'Automated and static', 5, 'pytest, syntax, API mapping, npm audit, pip check');
INSERT INTO audit_coverage VALUES ('1.5.1', 'Business runtime', 7, 'loan, payment, penalty, exports, PDFs, restore, database integrity');
INSERT INTO audit_coverage VALUES ('1.5.1', 'Interface', 4, 'desktop views, actions, 390 px navigation, clean console');
INSERT INTO audit_coverage VALUES ('1.5.1', 'Packaging', 4, 'Windows ZIP, macOS DMG, signature/checksum, native shutdown');
INSERT INTO audit_coverage VALUES ('1.5.1', 'Privacy and security', 4, 'public-source privacy, secret scan, dependency audit, bundle inspection');
