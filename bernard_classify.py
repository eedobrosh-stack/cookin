"""Section classification shared by build_db.py and server.py (ported from cookin shopping.js + supermarket aisles)."""
import re
SECTIONS = [  # id, emoji, Hebrew, English
 ("produce","🥬","ירקות ופירות","Fruit & veg"),("herbs","🌿","עשבי תיבול","Herbs"),("meatfish","🥩","בשר ודגים","Meat & fish"),
 ("dairy","🧀","חלב וביצים","Dairy & eggs"),("bakery","🥖","לחם ומאפים","Bakery"),("frozen","🧊","קפואים","Frozen"),
 ("canned","🥫","שימורים וצנצנות","Canned & jarred"),("dry","🍝","יבשים ודגנים","Dry goods & grains"),
 ("oils","🫒","שמנים ורטבים","Oils & sauces"),("spices","🧂","תבלינים","Spices"),("snacks","🍫","חטיפים ומתוקים","Snacks & sweets"),
 ("drinks","🥤","משקאות","Drinks"),("household","🧴","ניקיון ובית","Household"),("pharma","🧼","פארם ותינוקות","Pharm & baby"),
 ("other","🛒","אחר","Other")]
SEC_IDS = [s[0] for s in SECTIONS]
KW = [
 ("herbs",r"(פטרוזיליה|כוסברה|בזיליקום|נענע|שמיר|עירית|טימין|רוזמרין|מרווה|עשבי|אזוב|\b(parsley|cilantro|coriander|basil|mint|dill|chives|thyme|rosemary|sage|tarragon|herbs?)\b)"),
 ("meatfish",r"(עוף|חזה|שוק|כנפיים|בקר|בשר|כבש|הודו|סטייק|צלע|אנטריקוט|נקניק|בייקון|דג|סלמון|טונה טרייה|פילה|שרימפס|סרטנ|קלמרי|טחון|בריסקט|שניצל|קבב|המבורגר|\b(chicken|beef|lamb|pork|turkey|steak|ribs?|sausage|bacon|ham|meat|salmon|fish|cod|tilapia|shrimp|prawns?|squid|fillet|mince|schnitzel)\b)"),
 ("dairy",r"(חלב|שמנת|חמאה|גבינ|יוגורט|לאבנה|ביצ|טופו|פרמזן|מוצרלה|פטה|ריקוטה|מרגרינה|קשקבל|קוטג|לבן|שוקו|מעדן|\b(milk|cream|butter|cheese|yogh?urt|labneh|eggs?|tofu|parmesan|mozzarella|feta|ricotta|margarine)\b)"),
 ("bakery",r"(לחם|פיתה|פיתות|לחמני|באגט|בגט|חלה|בייגל|טורטייה|\b(bread|pita|baguette|bagel|challah|bun|tortilla)\b)"),
 ("frozen",r"(קפוא|גלידה|ארטיק|\b(frozen|ice cream)\b)"),
 ("canned",r"(שימורי|משומר|רסק עגבניות|קרם קוקוס|חלב קוקוס|זיתים|מלפפונים חמוצים|חמוצים|צלפים|טחינה|ריבה|במבוק|קופסת|תירס מקופסה|\b(canned|tinned|tomato paste|coconut (milk|cream)|olives?|pickles?|capers?|tahini|jam)\b)"),
 ("oils",r"(שמן|חומץ|רוטב|חרדל|קטשופ|מיונז|דבש|סילאן|ציר|סויה|\b(oil|vinegar|sauce|mustard|ketchup|mayo|honey|stock|broth)\b)"),
 ("drinks",r"(יין|בירה|וודקה|ויסקי|מיץ|סודה|קולה|משקה|תה|קפה|מים מינרליים|\b(wine|beer|vodka|whisk(e)?y|juice|soda|cola|tea|coffee|water)\b)"),
 ("spices",r"(מלח|פלפל שחור|פלפל לבן|פפריקה|כמון|כורכום|קינמון|תבלין|פתיתי צ'ילי|קארי|זעתר|אגוז מוסקט|אורגנו|קורט|\b(salt|pepper|paprika|cumin|turmeric|cinnamon|spice|seasoning|curry|nutmeg)\b)"),
 ("snacks",r"(שוקולד|במבה|ביסלי|חטיף|עוגיות|וופל|סוכריות|מסטיק|ממתק|\b(chocolate|candy|chips|snack|cookies?|wafers?|gum)\b)"),
 ("dry",r"(פסטה|ספגטי|אורז|אטריות|קמח|פירורי|סוכר|שיבולת|קוסקוס|עדשים|שעועית|אגוז|שקד|שומשום|גרעינ|קורנפלור|אבקת אפייה|קורנפלקס|דגני|פתיתים|גרנולה|\b(pasta|spaghetti|rice|noodles?|flour|breadcrumbs|sugar|oats|couscous|lentils?|beans|nuts?|almonds?|walnuts?|seeds?|cornstarch|baking|cereal)\b)"),
 ("household",r"(נייר טואלט|מגבות|שקיות|אבקת כביסה|מרכך כביסה|סבון כלים|אקונומיקה|ספוג|מטליות|נרות|צלחות|כוסות חד|\b(detergent|bleach|sponge|trash bags|toilet paper|paper towels?|candles?|napkins?)\b)"),
 ("pharma",r"(שמפו|מרכך שיער|דאודורנט|משחת שיניים|מברשת שיניים|חיתולים|מגבונים|תחבושות|טמפונים|סבון|קרם|גילוח|\b(shampoo|conditioner|deodorant|toothpaste|toothbrush|diapers?|wipes|soap|razor)\b)"),
 ("produce",r"(בצל|שום|ג'ינג'ר|עגבני|תפוח|גזר|מלפפון|לימון|ליים|גמבה|פלפל|כרוב|חסה|תרד|פטריות|קישוא|חציל|אבוקדו|בננה|תפוז|צ'ילי|תירס|סלרי|ברוקולי|כרובית|ירק|פרי|ענבים|אפרסק|אגס|תות|אבטיח|מלון|בטטה|דלורית|סלק|צנון|\b(onion|garlic|ginger|tomato|potato|carrot|cucumber|lemon|lime|cabbage|lettuce|spinach|mushroom|zucchini|eggplant|avocado|apple|banana|orange|chili|corn|celery|broccoli|cauliflower|scallion|vegetable|fruit)s?\b)"),
]
KW = [(s, re.compile(p, re.I)) for s, p in KW]
def classify(name):
    n = (name or "").strip().lower()
    for sec, rx in KW:
        if rx.search(n): return sec
    return "other"
# Rami Levy department / group -> section
def rl_section(dept, group, sub=""):
    g = group or ""
    if dept.startswith("פירות ירקות"):
        return "dry" if "פיצוח" in g else "produce"
    if dept.startswith("בשר"): return "meatfish"
    if dept.startswith("חלב ביצים"): return "dairy"
    if dept.startswith("לחם"): return "bakery"
    if dept.startswith("קפוא"): return "meatfish" if "נקניק" in g else "frozen"
    if dept.startswith("קטניות"): return "snacks" if "חטיפ" in g or "פריכ" in g else "dry"
    if dept.startswith("משקאות"): return "drinks"
    if dept.startswith("חטיפים"): return "snacks"
    if dept.startswith("פארם"): return "pharma"
    if dept.startswith("אחזקת") or dept.startswith("נייר") or dept.startswith("חגים"): return "household"
    if dept.startswith("שימורים"):
        if "שמן" in g or "רטבים" in g: return "oils"
        if "תבלינים" in g: return "spices"
        if "קמח" in g or "אפיה" in g: return "dry"
        return "canned"
    return classify(g + " " + sub) 
