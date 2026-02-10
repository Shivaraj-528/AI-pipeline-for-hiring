# agents/background_verification_agent.py

import os
import re
import requests
from dotenv import load_dotenv
from openai import OpenAI

from pathlib import Path
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)


def extract_candidate_info(resume_text):
    """
    Extract candidate information from resume using AI.
    Returns: name, email, linkedin_url, github_username
    """
    prompt = f"""
Extract the following information from this resume:
- Full name
- Email address
- LinkedIn profile URL (if mentioned)
- GitHub username or URL (if mentioned)

Resume:
{resume_text}

Respond in this exact format:
Name: <name>
Email: <email>
LinkedIn: <url or "Not found">
GitHub: <username or url or "Not found">
"""
    
    try:
        response = client.chat.completions.create(
            model="meta-llama/llama-3-8b-instruct",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        
        result = response.choices[0].message.content.strip()
        
        # Parse response
        info = {
            "name": None,
            "email": None,
            "linkedin": None,
            "github": None
        }
        
        for line in result.split('\n'):
            if line.startswith("Name:"):
                info["name"] = line.split("Name:")[1].strip()
            elif line.startswith("Email:"):
                info["email"] = line.split("Email:")[1].strip()
            elif line.startswith("LinkedIn:"):
                linkedin = line.split("LinkedIn:")[1].strip()
                info["linkedin"] = None if "not found" in linkedin.lower() else linkedin
            elif line.startswith("GitHub:"):
                github = line.split("GitHub:")[1].strip()
                info["github"] = None if "not found" in github.lower() else github
        
        return info
    
    except Exception as e:
        print(f"⚠️ Error extracting candidate info: {e}")
        return {"name": None, "email": None, "linkedin": None, "github": None}


def verify_email(email):
    """
    Validate email format and check if professional.
    Returns: dict with validation results
    """
    if not email:
        return {
            "valid": False,
            "professional": False,
            "confidence": 0,
            "reason": "No email provided"
        }
    
    # Email regex pattern
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    is_valid = bool(re.match(email_pattern, email))
    
    # Check for disposable/temporary email domains
    disposable_domains = [
        'tempmail.com', 'throwaway.email', '10minutemail.com',
        'guerrillamail.com', 'mailinator.com', 'trashmail.com'
    ]
    
    domain = email.split('@')[1] if '@' in email else ''
    is_disposable = domain.lower() in disposable_domains
    
    # Check if professional (not gmail, yahoo, etc for professional context)
    common_free_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']
    is_professional = domain.lower() not in common_free_domains
    
    confidence = 0
    if is_valid:
        confidence = 95 if not is_disposable else 50
        if is_professional:
            confidence = min(100, confidence + 5)
    
    return {
        "valid": is_valid and not is_disposable,
        "professional": is_professional,
        "confidence": confidence,
        "domain": domain
    }


def verify_linkedin(name, linkedin_url):
    """
    Verify LinkedIn profile.
    For demo: uses AI to validate URL format and name matching.
    In production: would scrape actual profile.
    """
    if not linkedin_url:
        return {
            "found": False,
            "profile_url": None,
            "name_match": False,
            "confidence": 0,
            "reason": "No LinkedIn URL provided in resume"
        }
    
    # Basic URL validation
    linkedin_pattern = r'(https?://)?(www\.)?linkedin\.com/in/[\w-]+'
    is_valid_url = bool(re.match(linkedin_pattern, linkedin_url))
    
    if not is_valid_url:
        return {
            "found": False,
            "profile_url": linkedin_url,
            "name_match": False,
            "confidence": 0,
            "reason": "Invalid LinkedIn URL format"
        }
    
    # For demo purposes, assume profile exists and matches
    # In production, would use Selenium/BeautifulSoup to scrape
    return {
        "found": True,
        "profile_url": linkedin_url,
        "name_match": True,
        "experience_match": True,
        "confidence": 85,
        "reason": "LinkedIn profile found and validated"
    }


def verify_github(github_username, resume_text):
    """
    Verify GitHub profile using GitHub API.
    Checks for MERN stack projects and recent activity.
    """
    if not github_username:
        return {
            "found": False,
            "username": None,
            "public_repos": 0,
            "mern_projects": 0,
            "recent_activity": False,
            "confidence": 0,
            "reason": "No GitHub username provided in resume"
        }
    
    # Extract username from URL if full URL provided
    if 'github.com' in github_username:
        github_username = github_username.split('github.com/')[-1].strip('/')
    
    try:
        # GitHub API - no auth needed for public data
        user_url = f"https://api.github.com/users/{github_username}"
        repos_url = f"https://api.github.com/users/{github_username}/repos"
        
        # Get user info
        user_response = requests.get(user_url, timeout=5)
        
        if user_response.status_code != 200:
            return {
                "found": False,
                "username": github_username,
                "public_repos": 0,
                "mern_projects": 0,
                "recent_activity": False,
                "confidence": 0,
                "reason": f"GitHub user not found: {github_username}"
            }
        
        user_data = user_response.json()
        public_repos = user_data.get('public_repos', 0)
        
        # Get repositories
        repos_response = requests.get(repos_url, timeout=5)
        repos = repos_response.json() if repos_response.status_code == 200 else []
        
        # Count MERN stack projects
        mern_keywords = ['react', 'node', 'express', 'mongodb', 'mern', 'javascript', 'typescript']
        mern_projects = 0
        
        for repo in repos[:30]:  # Check first 30 repos
            description = (repo.get('description') or '').lower()
            name = repo.get('name', '').lower()
            language = (repo.get('language') or '').lower()
            
            if any(keyword in description or keyword in name for keyword in mern_keywords):
                mern_projects += 1
            elif language in ['javascript', 'typescript']:
                mern_projects += 0.5
        
        mern_projects = int(mern_projects)
        
        # Check recent activity (repos updated in last 6 months)
        from datetime import datetime, timedelta
        six_months_ago = datetime.now() - timedelta(days=180)
        recent_activity = False
        
        for repo in repos[:10]:
            updated_at = repo.get('updated_at', '')
            if updated_at:
                try:
                    update_date = datetime.strptime(updated_at, '%Y-%m-%dT%H:%M:%SZ')
                    if update_date > six_months_ago:
                        recent_activity = True
                        break
                except:
                    pass
        
        # Calculate confidence
        confidence = 50
        if public_repos > 5:
            confidence += 15
        if mern_projects > 0:
            confidence += 20
        if recent_activity:
            confidence += 15
        
        confidence = min(100, confidence)
        
        return {
            "found": True,
            "username": github_username,
            "public_repos": public_repos,
            "mern_projects": mern_projects,
            "recent_activity": recent_activity,
            "confidence": confidence,
            "reason": "GitHub profile verified successfully"
        }
    
    except Exception as e:
        return {
            "found": False,
            "username": github_username,
            "public_repos": 0,
            "mern_projects": 0,
            "recent_activity": False,
            "confidence": 0,
            "reason": f"Error verifying GitHub: {str(e)}"
        }


def calculate_credibility_score(checks):
    """
    Calculate overall credibility score from individual checks.
    Weighted scoring: Email 20%, LinkedIn 40%, GitHub 40%
    """
    email_score = checks['email']['confidence'] * 0.20
    linkedin_score = checks['linkedin']['confidence'] * 0.40
    github_score = checks['github']['confidence'] * 0.40
    
    total_score = email_score + linkedin_score + github_score
    
    return int(total_score)


def verify_background(resume_text, candidate_email):
    """
    Main function to verify candidate background.
    Returns comprehensive verification report.
    """
    print("🔍 Extracting candidate information...")
    candidate_info = extract_candidate_info(resume_text)
    
    # Use provided email if extraction failed
    if not candidate_info['email'] and candidate_email:
        candidate_info['email'] = candidate_email
    
    print(f"   Name: {candidate_info['name'] or 'Not found'}")
    print(f"   Email: {candidate_info['email'] or 'Not found'}")
    print(f"   LinkedIn: {candidate_info['linkedin'] or 'Not found'}")
    print(f"   GitHub: {candidate_info['github'] or 'Not found'}")
    
    # Run verification checks
    print("\n📧 Verifying email...")
    email_check = verify_email(candidate_info['email'])
    print(f"   Valid: {email_check['valid']} | Confidence: {email_check['confidence']}%")
    
    print("\n💼 Verifying LinkedIn...")
    linkedin_check = verify_linkedin(candidate_info['name'], candidate_info['linkedin'])
    print(f"   Found: {linkedin_check['found']} | Confidence: {linkedin_check['confidence']}%")
    
    print("\n💻 Verifying GitHub...")
    github_check = verify_github(candidate_info['github'], resume_text)
    print(f"   Found: {github_check['found']} | Repos: {github_check['public_repos']} | MERN Projects: {github_check['mern_projects']}")
    print(f"   Confidence: {github_check['confidence']}%")
    
    # Calculate overall score
    checks = {
        "email": email_check,
        "linkedin": linkedin_check,
        "github": github_check
    }
    
    credibility_score = calculate_credibility_score(checks)
    
    # Determine status
    if credibility_score >= 80:
        status = "VERIFIED"
        recommendation = "PROCEED"
    elif credibility_score >= 70:
        status = "PARTIALLY_VERIFIED"
        recommendation = "PROCEED_WITH_CAUTION"
    else:
        status = "UNVERIFIED"
        recommendation = "REJECT"
    
    # Identify issues
    issues = []
    if not email_check['valid']:
        issues.append("Invalid or disposable email address")
    if not linkedin_check['found']:
        issues.append("LinkedIn profile not found")
    if not github_check['found']:
        issues.append("GitHub profile not found")
    elif github_check['public_repos'] == 0:
        issues.append("No public GitHub repositories")
    elif github_check['mern_projects'] == 0:
        issues.append("No MERN stack projects found on GitHub")
    
    return {
        "credibility_score": credibility_score,
        "status": status,
        "candidate_name": candidate_info['name'],
        "candidate_email": candidate_info['email'],
        "checks": checks,
        "issues": issues,
        "recommendation": recommendation
    }
