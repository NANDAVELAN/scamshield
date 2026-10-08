"""URL and indicator defanging utilities."""
import re

def defang(text: str) -> str:
    """Defang URLs and suspicious domain patterns so they cannot be clicked accidentally.
    
    Examples:
        http://evil.com/login -> hxxp://evil[.]com/login
        https://sbi-kyc.in -> hxxps://sbi-kyc[.]in
    """
    if not text:
        return ""
    # Defang http/https
    t = re.sub(r'https?://', lambda m: m.group(0).replace('http', 'hxxp'), text)
    # Defang common dot domains
    t = re.sub(r'([a-zA-Z0-9_-])\.([a-zA-Z]{2,10})', r'\1[.]\2', t)
    return t
