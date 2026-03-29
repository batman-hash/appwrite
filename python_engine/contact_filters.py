"""
Advanced Contact Filtering & Segmentation
Filters for: Junior devs, Frontend, Remote, Job seekers, Marketers, etc.
"""
import sqlite3
import os
import re
from typing import List, Dict, Tuple, Optional
from enum import Enum


class JobLevel(Enum):
    """Job level filtering"""
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    EXECUTIVE = "executive"


class DevSpecialty(Enum):
    """Developer specialties"""
    FRONTEND = "frontend"
    BACKEND = "backend"
    FULLSTACK = "fullstack"
    DEVOPS = "devops"
    MOBILE = "mobile"
    DATA = "data"
    ML = "machine_learning"
    QA = "qa"


class WorkMode(Enum):
    """Work mode preferences"""
    REMOTE = "remote"
    HYBRID = "hybrid"
    ONSITE = "onsite"


class ProfileMatcher:
    """Match contact profiles against job requirements"""
    
    # Keywords for filtering
    JUNIOR_KEYWORDS = [
        'junior', 'entry-level', 'entry level', 'beginner', 'trainee',
        'grad', 'graduate', 'intern', 'apprentice', 'newbie', 'entry',
        'first job', 'recent grad', 'newly', 'just started'
    ]
    
    FRONTEND_KEYWORDS = [
        'frontend', 'front-end', 'front end', 'react', 'vue', 'angular',
        'javascript', 'js', 'css', 'html', 'ui', 'ux', 'web design',
        'web developer', 'web development', 'typescript'
    ]
    
    BACKEND_KEYWORDS = [
        'backend', 'back-end', 'back end', 'python', 'java', 'node',
        'ruby', 'php', 'golang', 'go', 'api', 'database', 'server',
        'infrastructure', 'devops'
    ]
    
    REMOTE_KEYWORDS = [
        'remote', 'work from home', 'distributed', 'async', 'anywhere',
        'location independent', 'fully remote', 'home office', 'wfh'
    ]
    
    MARKETER_KEYWORDS = [
        'marketing', 'marketer', 'growth', 'social media', 'content',
        'sales', 'business development', 'brand', 'copywriter', 'seo',
        'ppc', 'paid', 'advertising', 'conversion'
    ]
    
    MONEY_MOTIVATED_KEYWORDS = [
        'money', 'earn', 'income', 'side hustle', 'passive income',
        'freelance', 'contract', 'hourly', 'commission', 'revenue',
        'profit', 'cash', 'paid', 'salary', 'bonus'
    ]
    
    JOB_SEEKER_KEYWORDS = [
        'hiring', 'job', 'opportunity', 'position', 'role', 'open',
        'looking for', 'looking forward', 'career', 'apply', 'interview',
        'resume', 'cv', '#hiringmyownteam', '#opentohire', '#jobseeker'
    ]
    
    REGISTERED_KEYWORDS = [
        'verified', 'confirmed', 'subscriber', 'member', 'registered member',
        'account holder', 'active user'
    ]
    
    @staticmethod
    def score_profile(profile: Dict) -> Dict:
        """
        Score a contact profile against criteria
        Returns match scores for different job types
        
        Args:
            profile: Contact profile with name, title, bio, etc.
        
        Returns {junior_score, frontend_score, remote_score, etc.}
        """
        text = ProfileMatcher._normalize_text(
            f"{profile.get('title', '')} {profile.get('bio', '')} "
            f"{profile.get('name', '')} {profile.get('company', '')} "
            f"{profile.get('email', '')} {profile.get('department', '')}"
        )
        
        return {
            'junior_developer': ProfileMatcher._score_junior(text),
            'frontend_developer': ProfileMatcher._score_frontend(text),
            'backend_developer': ProfileMatcher._score_backend(text),
            'remote_capable': ProfileMatcher._score_remote(text),
            'marketer': ProfileMatcher._score_marketer(text),
            'money_motivated': ProfileMatcher._score_money_motivated(text),
            'job_seeker': ProfileMatcher._score_job_seeker(text),
            'registered': ProfileMatcher._score_registered(text),
        }
    
    @staticmethod
    def _normalize_text(text: str) -> str:
        """Normalize text for matching"""
        return text.lower().strip() if text else ""
    
    @staticmethod
    def _score_junior(text: str) -> float:
        """Score for junior developer (0-100)"""
        score = 0
        
        # Check for junior keywords
        for keyword in ProfileMatcher.JUNIOR_KEYWORDS:
            if keyword in text:
                score += 25
        
        # Check for lack of senior keywords
        senior_keywords = ['senior', 'lead', 'principal', 'staff', 'architect']
        for keyword in senior_keywords:
            if keyword in text:
                score -= 30
        
        # Check for relevant tech
        if any(tech in text for tech in ['javascript', 'python', 'java', 'react', 'node']):
            score += 20
        
        # Check years of experience (if mentioned)
        if re.search(r'(\d+)\s*(?:years?|yrs?|y)', text):
            match = re.search(r'(\d+)\s*(?:years?|yrs?|y)', text)
            years = int(match.group(1))
            if 0 < years < 3:
                score += 30
            elif years >= 5:
                score -= 20
        
        return min(100, max(0, score))
    
    @staticmethod
    def _score_frontend(text: str) -> float:
        """Score for frontend developer (0-100)"""
        score = 0
        
        # Check frontend keywords
        for keyword in ProfileMatcher.FRONTEND_KEYWORDS:
            if keyword in text:
                score += 15
        
        # Check for popular frontend frameworks/languages
        frontend_stack = {
            'react': 20,
            'vue': 20,
            'angular': 20,
            'typescript': 15,
            'css': 10,
            'html': 10,
            'javascript': 10,
            'tailwind': 15,
            'nextjs': 20,
            'ui': 10,
            'ux': 10
        }
        
        for tech, points in frontend_stack.items():
            if tech in text:
                score += points
        
        return min(100, max(0, score))
    
    @staticmethod
    def _score_backend(text: str) -> float:
        """Score for backend developer (0-100)"""
        score = 0
        
        # Check backend keywords
        for keyword in ProfileMatcher.BACKEND_KEYWORDS:
            if keyword in text:
                score += 15
        
        # Backend tech stack
        backend_stack = {
            'python': 20,
            'java': 20,
            'node': 20,
            'ruby': 15,
            'golang': 15,
            'rust': 15,
            'database': 15,
            'sql': 10,
            'api': 10,
            'devops': 15
        }
        
        for tech, points in backend_stack.items():
            if tech in text:
                score += points
        
        return min(100, max(0, score))
    
    @staticmethod
    def _score_remote(text: str) -> float:
        """Score for remote work preference (0-100)"""
        score = 0
        
        for keyword in ProfileMatcher.REMOTE_KEYWORDS:
            if keyword in text:
                score += 30
        
        # Negative if location-specific
        if 'onsite' in text or 'office' in text:
            score -= 30
        
        return min(100, max(0, score))
    
    @staticmethod
    def _score_marketer(text: str) -> float:
        """Score for marketing professional (0-100)"""
        score = 0
        
        for keyword in ProfileMatcher.MARKETER_KEYWORDS:
            if keyword in text:
                score += 20
        
        return min(100, max(0, score))
    
    @staticmethod
    def _score_money_motivated(text: str) -> float:
        """Score for money motivation (0-100)"""
        score = 0
        
        for keyword in ProfileMatcher.MONEY_MOTIVATED_KEYWORDS:
            if keyword in text:
                score += 20
        
        # Freelancers, contractors are usually money motivated
        if any(w in text for w in ['freelancer', 'contractor', 'consultant']):
            score += 30
        
        return min(100, max(0, score))
    
    @staticmethod
    def _score_job_seeker(text: str) -> float:
        """Score for job seeker (0-100)"""
        score = 0
        
        for keyword in ProfileMatcher.JOB_SEEKER_KEYWORDS:
            if keyword in text:
                score += 15
        
        # Hashtags specifically for job seeking
        if '#hiringmyownteam' in text or '#opentohire' in text:
            score += 50
        
        return min(100, max(0, score))
    
    @staticmethod
    def _score_registered(text: str) -> float:
        """Score for registered/active user (0-100)"""
        score = 0
        
        for keyword in ProfileMatcher.REGISTERED_KEYWORDS:
            if keyword in text:
                score += 50
        
        # If they have a complete profile, they're registered
        if text and len(text) > 50:
            score += 30
        
        return min(100, max(0, score))


class ContactFilter:
    """Filter contacts by criteria"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.getenv('DATABASE_PATH', './database/devnav.db')
        self.db_path = db_path
    
    def filter_junior_developers(self, min_score: int = 60) -> Tuple[int, List[Dict]]:
        """Get junior developer contacts"""
        return self._filter_by_profile('junior_developer', min_score)
    
    def filter_frontend_developers(self, min_score: int = 60) -> Tuple[int, List[Dict]]:
        """Get frontend developer contacts"""
        return self._filter_by_profile('frontend_developer', min_score)
    
    def filter_remote_capable(self, min_score: int = 50) -> Tuple[int, List[Dict]]:
        """Get contacts interested in remote work"""
        return self._filter_by_profile('remote_capable', min_score)
    
    def filter_marketers(self, min_score: int = 60) -> Tuple[int, List[Dict]]:
        """Get marketing professionals"""
        return self._filter_by_profile('marketer', min_score)
    
    def filter_money_motivated(self, min_score: int = 50) -> Tuple[int, List[Dict]]:
        """Get money-motivated people"""
        return self._filter_by_profile('money_motivated', min_score)
    
    def filter_job_seekers(self, min_score: int = 70) -> Tuple[int, List[Dict]]:
        """Get active job seekers"""
        return self._filter_by_profile('job_seeker', min_score)
    
    def filter_by_multiple_criteria(self, criteria: Dict[str, int] = None) -> Tuple[int, List[Dict]]:
        """
        Filter by multiple criteria
        
        Args:
            criteria: {
                'junior_developer': 70,
                'frontend_developer': 60,
                'remote_capable': 50
            }
        """
        if criteria is None:
            criteria = {
                'junior_developer': 70,
                'frontend_developer': 60,
                'remote_capable': 50,
                'job_seeker': 60
            }
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM contacts WHERE title IS NOT NULL OR department IS NOT NULL")
        all_contacts = cursor.fetchall()
        conn.close()
        
        matches = []
        for contact in all_contacts:
            profile = dict(contact)
            scores = ProfileMatcher.score_profile(profile)
            
            # Check if meets all criteria
            meets_criteria = True
            for criterion, min_score in criteria.items():
                if scores.get(criterion, 0) < min_score:
                    meets_criteria = False
                    break
            
            if meets_criteria:
                profile['scores'] = scores
                profile['match_types'] = [k for k, v in criteria.items() 
                                         if scores.get(k, 0) >= v]
                matches.append(profile)
        
        return len(matches), matches
    
    def _filter_by_profile(self, profile_type: str, min_score: int) -> Tuple[int, List[Dict]]:
        """Generic filter by profile score"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM contacts WHERE title IS NOT NULL OR department IS NOT NULL")
        all_contacts = cursor.fetchall()
        conn.close()
        
        matches = []
        for contact in all_contacts:
            profile = dict(contact)
            scores = ProfileMatcher.score_profile(profile)
            
            if scores.get(profile_type, 0) >= min_score:
                profile['score'] = scores[profile_type]
                matches.append(profile)
        
        # Sort by score descending
        matches.sort(key=lambda x: x['score'], reverse=True)
        return len(matches), matches


def get_contact_filter(db_path: str = None) -> ContactFilter:
    """Factory function"""
    return ContactFilter(db_path)


if __name__ == "__main__":
    # Test scoring
    test_profile = {
        'name': 'John Smith',
        'title': 'Junior Frontend Developer',
        'bio': 'React specialist, looking for remote work opportunities #opentohire',
        'email': 'john@gmail.com',
        'company': 'Freelance',
        'department': 'Technology'
    }
    
    scores = ProfileMatcher.score_profile(test_profile)
    print("Profile Scores:")
    for key, score in scores.items():
        print(f"  {key}: {score:.1f}")
    
    # Test filtering
    filter_obj = ContactFilter()
    count, juniors = filter_obj.filter_junior_developers(min_score=50)
    print(f"\nJunior developers found: {count}")
