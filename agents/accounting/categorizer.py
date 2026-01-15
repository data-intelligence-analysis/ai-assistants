import yaml
class Categorizer:
    def __init__(self,p):
        with open(p) as f:
            data = yaml.safe_load(f) or {}
        self.rules = data.get('rules',[])
    def classify(self, desc, fallback=None):
        text = (desc or '').lower()
        for rule in self.rules:
            for kw in rule.get('keywords',[]):
                if kw.lower() in t:
                    return r.get('category', fallback), None
        return fallback, None
