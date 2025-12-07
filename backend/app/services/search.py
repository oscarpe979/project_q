from sqlmodel import Session, select, col, or_, and_
from typing import List, Optional
from datetime import datetime, date
from dateutil import parser
from backend.app.db.models import Voyage, ScheduleItem, VoyageItinerary, VenueSchedule
import re

class SearchService:
    def __init__(self, session: Session):
        self.session = session

    def search_schedules(self, query_str: str, venue_id: int, skip: int = 0, limit: int = 20) -> List[Voyage]:
        """
        Search for voyages using fuzzy matching for robust results.
        Handles typos (Tokio -> Tokyo), plurals (Cartagenas -> Cartagena), and partial matches.
        """
        # If no query, return standard sorted list with SQL pagination
        if not query_str:
            return self._get_all_schedules(venue_id, skip=skip, limit=limit)

        query_str = query_str.strip().lower()

        # 1. Fetch all candidate data (eager load for in-memory filtering)
        # Note: Efficient for <1000 schedules. For larger scales, use a search engine.
        candidates = self._get_all_schedules(venue_id)
        
        # 2. Build search index for scoring (avoids N+1 by fetching related data in bulk)
        search_data = self._build_search_index(venue_id)
        
        scored_results = []
        
        # 2. Score each voyage
        for voyage in candidates:
            score = 0
            
            # Exact/Partial match on Voyage Number
            if query_str in voyage.voyage_number.lower():
                score += 100
            
            # Smart Date Parsing (keep existing logic)
            date_range = self._parse_date_query(query_str)
            if date_range:
                start, end = date_range
                if voyage.start_date <= end and voyage.end_date >= start:
                    score += 50
            
            # Fuzzy match on content (Ports, Events, Notes)
            content_text = search_data.get(voyage.id, "")
            fuzzy_score = self._calculate_fuzzy_score(query_str, content_text)
            score += fuzzy_score
            
            if score > 0:
                scored_results.append((score, voyage))
                
        # 3. Sort by score desc, then date desc
        scored_results.sort(key=lambda x: (x[0], x[1].start_date), reverse=True)
        
        return [x[1] for x in scored_results][skip : skip + limit]

    def _calculate_fuzzy_score(self, query: str, text: str) -> int:
        """
        Calculates a match score based on containment and string similarity.
        """
        text = text.lower()
        
        # 1. Direct containment (fastest and strongest for "Cartagenas" -> "Cartagena" if query is substring)
        # Check if query is in text or text is in query (reverse containment for "Cartagenas" query matching "Cartagena" text?)
        # User example: Query "Cartagenas" (user typed pl), Text has "Cartagena". 
        # "Cartagena" is in "Cartagenas".
        
        # Split text into tokens (words)
        tokens = text.split()
        max_token_score = 0
        
        import difflib
        
        for token in tokens:
            # Clean token
            token = token.strip(".,;:()[]")
            
            if not token:
                continue
                
            # Perfect match
            if query == token:
                return 50
            
            # Containment
            # 1. Query inside Token ("install" matches "installation") - ALWAYS GOOD
            if query in token:
                return 40
                
            # 2. Token inside Query ("installation" matches "install") - DANGEROUS for short tokens
            # Example bug: Query "install" matches token "in" or "all".
            # Fix: Only allow if token is significant length (e.g., > 3 chars)
            if len(token) > 3 and token in query:
                return 40
                
            # Fuzzy ratio (for Tokio vs Tokyo)
            # quick optimization: if lengths are wildly different, skip
            if abs(len(query) - len(token)) > 3:
                continue
                
            ratio = difflib.SequenceMatcher(None, query, token).ratio()
            if ratio > 0.7: # Lower threshold to catch "Tokio" (0.8) reliably
                max_token_score = max(max_token_score, int(ratio * 40))
                
        return max_token_score

    def _build_search_index(self, venue_id: int) -> dict:
        """
        Returns a dictionary mapping voyage_id to a searchable text string.
        Includes: Itinerary Locations, Event Titles, Event Types, Notes.
        """
        # Fetch Itineraries
        itineraries = self.session.exec(
            select(VoyageItinerary.voyage_id, VoyageItinerary.location)
            .where(VoyageItinerary.voyage_id.in_(
                select(VenueSchedule.voyage_id).where(VenueSchedule.venue_id == venue_id)
            ))
        ).all()
        
        # Fetch Schedule Items
        schedule_items = self.session.exec(
            select(ScheduleItem.voyage_id, ScheduleItem.title, ScheduleItem.type, ScheduleItem.notes)
            .where(ScheduleItem.venue_id == venue_id)
        ).all()
        
        index = {}
        
        for vid, loc in itineraries:
            index[vid] = index.get(vid, "") + " " + (loc or "")
            
        for vid, title, type_, notes in schedule_items:
            index[vid] = index.get(vid, "") + " " + (title or "") + " " + (type_ or "") + " " + (notes or "")
            
        return index

    def _get_all_schedules(self, venue_id: int, skip: int = 0, limit: int = 0) -> List[Voyage]:
        query = select(Voyage).join(VenueSchedule).where(VenueSchedule.venue_id == venue_id).order_by(Voyage.voyage_number.desc(), Voyage.start_date.desc())
        
        # Apply pagination if limit is set (limit=0 means fetch all, used by search internal logic)
        if limit > 0:
            query = query.offset(skip).limit(limit)
            
        return self.session.exec(query).all()

    def _parse_date_query(self, query: str) -> Optional[tuple[date, date]]:
        """
        Attempts to parse vague date strings like "September 2025", "Sep 25", "2025".
        Returns (start_date, end_date) range or None.
        """
        # Regex patterns for partial dates
        
        # Year only: "2025"
        year_match = re.fullmatch(r"(\d{4})", query)
        if year_match:
            year = int(year_match.group(1))
            return date(year, 1, 1), date(year, 12, 31)

        # Month Year: "September 2025", "Sep 2025", "09/2025", "09/25"
        try:
            # parser.parse is powerful but aggressive. Let's try it.
            # default=datetime(2025, 1, 1) to fill missing parts? No, default is current date usually.
            # We want to detect resolution.
            
            dt = parser.parse(query, fuzzy=True)
            
            # Heuristic: If user typed "September 2025", we want the whole month.
            # parser gives us a specific instant.
            # Let's check if the query contains a year.
            has_year = bool(re.search(r"\d{4}", query)) or bool(re.search(r"/\d{2}$", query))
            
            # If we detected a valid date, let's assume month granularity if day is 1 (default?) 
            # or try to infer from string length/format. 
            # Actually, `dateutil` doesn't easily tell us "what was parsed".
            
            # Custom simple parsing for Month/Year is safer.
            months = {
                'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
                'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
                'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12
            }
            
            lower_q = query.lower()
            found_month = None
            for name, num in months.items():
                if name in lower_q:
                    found_month = num
                    break
            
            found_year = year_match.group(1) if year_match else None
            if not found_year:
                # Find 4 digits
                y_m = re.search(r"\d{4}", query)
                if y_m:
                    found_year = int(y_m.group(0))
                else: 
                     # Try 2 digits at end? "Sep 25"
                     y_m2 = re.search(r"\b\d{2}$", query)
                     if y_m2:
                         val = int(y_m2.group(0))
                         found_year = 2000 + val if val < 100 else val # Assumption 20xx
            
            if found_month and found_year:
                from calendar import monthrange
                mr = monthrange(found_year, found_month)
                return date(found_year, found_month, 1), date(found_year, found_month, mr[1])
            
            # If simple date "09/25/2025" -> Single day range
            # If parser worked, return that day
            return dt.date(), dt.date()

        except Exception:
            return None
