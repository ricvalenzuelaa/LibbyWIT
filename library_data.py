"""
Verified Library Information and Knowledge Base for Western Institute of Technology (WIT) Library.
Contains verified factual information across all 10 supported library categories.
"""

from typing import Dict, Any, List

VERIFIED_LIBRARY_DATA: Dict[str, Dict[str, Any]] = {
    "book_information": {
        "title": "Book Information & Classification",
        "description": "General book details, genres, subjects, summaries, and shelving organization.",
        "verified_facts": (
            "The WIT Library holds textbooks, reference volumes, fiction, non-fiction, and academic literature. "
            "Materials are organized on the shelves according to the Dewey Decimal Classification (DDC) system. "
            "For publication specifics, edition details, or call numbers of specific titles, consult the library catalog or the reference desk."
        )
    },
    "library_hours_location": {
        "title": "Library Hours, Location & Contact",
        "description": "Operating schedule, campus address, and contact information.",
        "verified_facts": (
            "Operating Schedule: Monday to Friday: 8:00 AM - 6:00 PM; Saturday: 9:00 AM - 1:00 PM. "
            "Closed on Sundays and official school/national holidays. "
            "Location: Main Campus Building, Western Institute of Technology (WIT), La Paz, Iloilo City, Philippines. "
            "Contact: Email: library@wit.edu.ph, or consult the circulation desk on the main floor."
        )
    },
    "borrowing_returning": {
        "title": "Borrowing, Returning, Renewals & Penalties",
        "description": "Circulation limits, loan durations, return procedures, renewals, and overdue fines.",
        "verified_facts": (
            "Borrowing Limits: Enrolled students may borrow up to three (3) general circulation books at a time. "
            "Loan Period: Seven (7) calendar days for general circulation books. Reference materials, periodicals, and thesis copies are for room-use only. "
            "Renewals: Books may be renewed once for an additional 7 days at the circulation desk if no other patron has placed a hold on the title. "
            "Returns: Books must be returned to the circulation desk or designated book drop during operating hours. "
            "Overdue Fines: Php 5.00 per school day per overdue book. Borrowing privileges are suspended until overdue items are returned and outstanding fines are settled. "
            "Lost or Damaged Items: Must be reported immediately; borrower must replace the book with an acceptable copy of the same or newer edition, or pay the assessed replacement value plus processing fees."
        )
    },
    "book_availability_catalog": {
        "title": "Book Availability & Catalog Search",
        "description": "Catalog searches, checking holdings, shelf locations, and book reservations.",
        "verified_facts": (
            "Catalog Connection Status: This chatbot does NOT have a live connection to the active WIT circulation database or real-time shelf status. "
            "How to Check Availability: To verify if a specific title is currently in stock or on the shelf, search the official WIT OPAC (Online Public Access Catalog) terminals on campus or ask a library staff member at the circulation desk. "
            "Call Numbers: Physical books are arranged by Dewey Decimal Classification call numbers displayed on the spine. "
            "Reservations / Holds: If a desired circulating book is currently checked out by another student, you can place a hold request at the circulation desk."
        )
    },
    "facilities_services": {
        "title": "Facilities & Services",
        "description": "Study areas, computer access, Wi-Fi, printing, scanning, and reference assistance.",
        "verified_facts": (
            "Study Areas: Quiet reading halls, individual study carrels, and group discussion tables. "
            "Computers & Internet: Computer workstations with internet connectivity for academic research, plus campus Wi-Fi access for students. "
            "Printing & Scanning: Document printing, photocopying, and scanning services are available for academic materials in compliance with copyright regulations. "
            "Reference Assistance: Professional librarians provide one-on-one assistance with research formulation and locating scholarly resources."
        )
    },
    "membership_accounts": {
        "title": "Membership & Library Accounts",
        "description": "Library registration, student IDs, card validity, and account maintenance.",
        "verified_facts": (
            "Eligibility: All officially enrolled WIT students, faculty members, and staff. "
            "Registration Requirements: Present your valid WIT student ID and current semester Certificate of Matriculation / enrollment assessment form at the circulation desk. "
            "Validity: Library registration is valid for the current academic semester / school year and is renewed upon enrollment in the succeeding term. "
            "Lost ID / Card: Report lost IDs immediately to the circulation desk to freeze borrowing activity and obtain account replacement assistance."
        )
    },
    "research_academic_assistance": {
        "title": "Research & Academic Assistance",
        "description": "Citation guides (APA, MLA, IEEE), academic database search strategies, and scholarly resources.",
        "verified_facts": (
            "Citation Support: Guidance on formatting reference lists and in-text citations using APA 7th edition, MLA 9th edition, or IEEE standards. "
            "Search Techniques: Librarians can guide you on Boolean search operators (AND, OR, NOT), subject headings, and keywords to find peer-reviewed papers. "
            "Theses & Special Collections: Undergraduate theses, capstone projects, and special reference archives are accessible in the reference section for room-use only."
        )
    },
    "digital_resources": {
        "title": "Digital Resources & Electronic Access",
        "description": "E-books, online journals, academic databases, and remote access instructions.",
        "verified_facts": (
            "Online Databases: WIT Library provides access to subscribed academic databases, digital repositories, and open-access collections. "
            "Access Instructions: E-resources and e-journals are accessed through the official WIT student portal using your student credentials. "
            "Remote Access: Off-campus access is available by logging into the student portal with your institutional account."
        )
    },
    "book_recommendations": {
        "title": "Book Recommendations & Discovery",
        "description": "Subject, genre, and academic reading recommendations.",
        "verified_facts": (
            "Recommendations Policy: The chatbot can provide reading and study recommendations based on general literary and academic knowledge. "
            "Verification Notice: Recommended titles should be checked against the WIT Library OPAC or with library staff to confirm whether a physical copy is currently held in the library's collection."
        )
    },
    "rules_policies": {
        "title": "Library Rules & Code of Conduct",
        "description": "Library conduct, noise policy, food/drinks, computer usage, and material handling.",
        "verified_facts": (
            "Quiet Zone: Silence must be observed in study areas and reading rooms; conversations should be kept minimal and low. "
            "Mobile Phones: Keep devices in silent or vibrate mode. Phone calls must be answered outside the library. "
            "Food & Drinks: Strictly no food, snacks, or uncovered drinks allowed inside reading and computer areas (sealed water bottles only in designated zones). "
            "Bag Deposit: Large backpacks and personal bags must be deposited in the designated entrance cubicles/shelves. "
            "Care of Materials: Patrons must not mark, write, fold, or damage library books and property."
        )
    }
}

def get_verified_knowledge_text() -> str:
    """Generate a clean, structured text representation of all verified facts for system prompts."""
    lines = ["VERIFIED WIT LIBRARY INFORMATION:"]
    for cat_key, cat_data in VERIFIED_LIBRARY_DATA.items():
        lines.append(f"\n[{cat_data['title']}]")
        lines.append(f"{cat_data['verified_facts']}")
    return "\n".join(lines)

def get_intent_answer(intent_name: str) -> str:
    """Return verified factual answer corresponding to traditional intent keys."""
    mapping = {
        "library_hours": VERIFIED_LIBRARY_DATA["library_hours_location"]["verified_facts"],
        "operating_hours": VERIFIED_LIBRARY_DATA["library_hours_location"]["verified_facts"],
        "borrowing": VERIFIED_LIBRARY_DATA["borrowing_returning"]["verified_facts"],
        "borrowing_limit": "Enrolled students may borrow up to three (3) general circulation books at a time for seven (7) days.",
        "loan_period": "General circulation books may be borrowed for up to 7 calendar days.",
        "renew_book": "Books may be renewed once for an additional 7 days at the circulation desk if no hold has been placed.",
        "return_book": "Please return books to the circulation desk or book drop during library operating hours.",
        "penalties": VERIFIED_LIBRARY_DATA["borrowing_returning"]["verified_facts"],
        "overdue_fines": "Overdue fines are Php 5.00 per school day per overdue book. Settle fines at the circulation desk.",
        "library_card": VERIFIED_LIBRARY_DATA["membership_accounts"]["verified_facts"],
        "library_card_apply": "Present your valid student ID and current semester Certificate of Matriculation at the circulation desk.",
        "catalog_availability": VERIFIED_LIBRARY_DATA["book_availability_catalog"]["verified_facts"],
        "book_availability": VERIFIED_LIBRARY_DATA["book_availability_catalog"]["verified_facts"],
        "citation_help": VERIFIED_LIBRARY_DATA["research_academic_assistance"]["verified_facts"],
        "citation_apa": "Follow APA 7th edition formatting: Author, Year, Title, Source/DOI. Ask the reference desk for style sheets.",
        "citation_mla": "Follow MLA 9th edition formatting: Author, Title, Container, Date. Reference librarians can assist.",
        "facilities_services": VERIFIED_LIBRARY_DATA["facilities_services"]["verified_facts"],
        "library_rules": VERIFIED_LIBRARY_DATA["rules_policies"]["verified_facts"],
        "library_location": "Main Campus Building, Western Institute of Technology (WIT), La Paz, Iloilo City, Philippines.",
        "e_resources": VERIFIED_LIBRARY_DATA["digital_resources"]["verified_facts"],
        "contact_librarian": "Contact the WIT Library via email at library@wit.edu.ph or visit the circulation and reference desks.",
    }
    return mapping.get(intent_name, "")
