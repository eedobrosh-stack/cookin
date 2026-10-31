"""Pawed legal pages: Terms of use, Privacy policy, and the Takedown / data request form (English + Hebrew).

DRAFT for review by a lawyer. Edit the OPERATOR block below before relying on any of this text.
Routes (wired in vidsum_articles.handle_get / handle_post): /vidsum/terms, /vidsum/privacy, /vidsum/takedown, POST /api/vidsum/takedown.
Requests are stored in the app database (table takedown_requests); admins read them at GET /api/vidsum/admin/takedowns.
"""
import html as _html
import json
import re
import threading
import time

import multiuser

# ---------------------------------------------------------------- edit these
OPERATOR = "Eedo Brosh"            # who runs Pawed (shown as the controller of personal data)
OPERATOR_HE = "עידו ברוש"
COUNTRY = "Israel"
COUNTRY_HE = "ישראל"
EFFECTIVE = "1 November 2026"
EFFECTIVE_HE = "1 בנובמבר 2026"
SITE = "pawed.io"
RESPONSE_DAYS = 7                  # promised first response time for takedown requests
# -----------------------------------------------------------------------------

KINDS = {
    "copyright": ("Copyright or content removal (rights holder / show owner)", "זכויות יוצרים או הסרת תוכן (בעל זכויות / בעל הפודקאסט)"),
    "inaccurate": ("Inaccurate or harmful statement about me", "קביעה לא מדויקת או פוגענית לגביי"),
    "privacy": ("Privacy: access, correct or delete my data", "פרטיות: עיון, תיקון או מחיקה של המידע שלי"),
    "optout": ("Opt my show out of Pawed", "הוצאת הפודקאסט שלי מ-Pawed"),
    "other": ("Something else", "אחר"),
}

# ------------------------------------------------------------------ texts
TERMS = {
    "en": f"""
<h1>Terms of use</h1>
<p class="eff">Effective {EFFECTIVE}. Draft, pending legal review.</p>

<h2>1. What Pawed is</h2>
<p>Pawed ({SITE}) is an independent news portal that publishes short, automatically generated summaries of publicly available podcasts and videos, with a link to the original episode. Pawed is operated by {OPERATOR}, {COUNTRY}. Pawed is not affiliated with, sponsored by or endorsed by any podcast, creator, YouTube, Spotify or Apple.</p>

<h2>2. AI-generated summaries, accuracy</h2>
<p>Summaries are compiled automatically from transcripts of the original audio or video, using artificial intelligence. They can contain mistakes, omissions or wrong attributions. Opinions in a summary are those of the people speaking in the original episode, not of Pawed, and have not been verified. Nothing on Pawed is legal, financial, medical or other professional advice. Please check the original episode before relying on or repeating anything.</p>

<h2>3. Third-party content and intellectual property</h2>
<p>Episodes, recordings, names, logos and artwork belong to their owners. Pawed shows brief excerpts, short quotations and summaries for the purposes of reporting and commentary, always with attribution and a link to the original. If you own rights in content shown on Pawed, or you run a show and prefer not to be featured, use the <a href="/vidsum/takedown">takedown form</a>. We review requests promptly, and may remove an article or a whole show.</p>

<h2>4. Your account</h2>
<p>You can use Pawed without an account. To add your own sources, rate stories or save preferences you sign in with Google. You are responsible for activity under your account. Sources and episodes you add are private to you unless you are an administrator. By submitting a link you confirm that it points to publicly available content and that you may ask for it to be summarised. We may remove any source or episode, and may suspend accounts that break these terms.</p>

<h2>5. Acceptable use</h2>
<p>Do not: scrape or copy Pawed in bulk, use bots or automated access beyond normal browsing, republish or resell Pawed summaries, try to bypass limits or security, disrupt the service, submit unlawful content, or use Pawed to harass anyone.</p>

<h2>6. Licence</h2>
<p>You may read Pawed and share links to its articles for personal, non-commercial use. All other rights in the Pawed site, design and its own text are reserved.</p>

<h2>7. Takedown and complaints</h2>
<p>Requests to remove or correct content, and rights-holder notices, are handled through the <a href="/vidsum/takedown">takedown form</a>. Accounts of repeat infringers may be closed.</p>

<h2>8. No warranty, limited liability</h2>
<p>Pawed is provided "as is" and "as available", without warranties of any kind. To the fullest extent permitted by law, Pawed and its operator are not liable for indirect or consequential loss, loss of profit or data, or for reliance on a summary. Nothing in these terms limits liability that cannot be limited by law, or your statutory consumer rights.</p>

<h2>9. Changes</h2>
<p>We may update these terms and the date above. Continuing to use Pawed after a change means you accept it.</p>

<h2>10. Governing law</h2>
<p>These terms are governed by the laws of {COUNTRY}. The competent courts in {COUNTRY} have jurisdiction, without affecting mandatory consumer protections where you live.</p>

<h2>11. Contact</h2>
<p>Use the <a href="/vidsum/takedown">contact and takedown form</a>.</p>
""",
    "he": f"""
<h1>תנאי שימוש</h1>
<p class="eff">בתוקף מ-{EFFECTIVE_HE}. טיוטה, בכפוף לבדיקה משפטית.</p>

<h2>1. מהו Pawed</h2>
<p>Pawed ({SITE}) הוא פורטל חדשות עצמאי המפרסם סיכומים קצרים שנוצרים אוטומטית של פודקאסטים וסרטונים זמינים לציבור, עם קישור לפרק המקורי. Pawed מופעל על ידי {OPERATOR_HE}, {COUNTRY_HE}. Pawed אינו קשור לאף פודקאסט, יוצר, YouTube, Spotify או Apple, אינו ממומן על ידם ואינו מאושר על ידם.</p>

<h2>2. סיכומים שנוצרו בבינה מלאכותית, דיוק</h2>
<p>הסיכומים נערכים אוטומטית מתוך תמלול של האודיו או הווידאו המקורי באמצעות בינה מלאכותית. הם עלולים להכיל טעויות, השמטות או ייחוס שגוי. הדעות בסיכום הן של הדוברים בפרק המקורי ולא של Pawed, ולא נבדקו. שום דבר ב-Pawed אינו ייעוץ משפטי, פיננסי, רפואי או מקצועי אחר. מומלץ לבדוק את הפרק המקורי לפני הסתמכות או ציטוט.</p>

<h2>3. תוכן צד שלישי וקניין רוחני</h2>
<p>הפרקים, ההקלטות, השמות, הלוגואים והעטיפות שייכים לבעליהם. Pawed מציג קטעים קצרים, ציטוטים קצרים וסיכומים לצורכי דיווח וביקורת, תמיד עם ייחוס וקישור למקור. אם אתם בעלי זכויות בתוכן המוצג, או מפעילים פודקאסט שאינכם מעוניינים להיות מוצגים בו, השתמשו ב<a href="/vidsum/takedown">טופס ההסרה</a>. נבדוק פניות במהירות, ועשויים להסיר כתבה או פודקאסט שלם.</p>

<h2>4. החשבון שלכם</h2>
<p>אפשר להשתמש ב-Pawed בלי חשבון. כדי להוסיף מקורות משלכם, לדרג כתבות או לשמור העדפות נכנסים עם Google. אתם אחראים לפעילות בחשבונכם. מקורות ופרקים שתוסיפו גלויים רק לכם, אלא אם אתם מנהלים. בשליחת קישור אתם מאשרים שהוא מצביע על תוכן זמין לציבור ושמותר לבקש לסכם אותו. אנו רשאים להסיר כל מקור או פרק, ולהשעות חשבונות שמפרים את התנאים.</p>

<h2>5. שימוש מותר</h2>
<p>אסור: לשאוב או להעתיק את Pawed בהיקף גדול, להשתמש בבוטים או בגישה אוטומטית מעבר לגלישה רגילה, לפרסם מחדש או למכור סיכומים של Pawed, לנסות לעקוף מגבלות או אבטחה, לשבש את השירות, להגיש תוכן בלתי חוקי או להשתמש ב-Pawed כדי להטריד אחרים.</p>

<h2>6. רישיון</h2>
<p>מותר לקרוא את Pawed ולשתף קישורים לכתבות לשימוש אישי ולא מסחרי. כל הזכויות האחרות באתר, בעיצוב ובטקסטים של Pawed שמורות.</p>

<h2>7. בקשות הסרה ותלונות</h2>
<p>בקשות להסרה או לתיקון תוכן והודעות של בעלי זכויות מטופלות דרך <a href="/vidsum/takedown">טופס ההסרה</a>. חשבונות של מפרים חוזרים עשויים להיסגר.</p>

<h2>8. ללא אחריות, הגבלת חבות</h2>
<p>Pawed ניתן "כמות שהוא" ו"כפי שזמין", ללא אחריות מכל סוג. במידה המרבית המותרת בדין, Pawed ומפעילו אינם אחראים לנזק עקיף או תוצאתי, לאובדן רווח או מידע, או להסתמכות על סיכום. דבר בתנאים אלה אינו מגביל אחריות שאין אפשרות להגביל על פי דין, או זכויות צרכן שבדין.</p>

<h2>9. שינויים</h2>
<p>אנו רשאים לעדכן את התנאים ואת התאריך שלמעלה. המשך שימוש ב-Pawed לאחר שינוי מהווה הסכמה לו.</p>

<h2>10. דין חל</h2>
<p>על תנאים אלה יחולו דיני {COUNTRY_HE}. לבתי המשפט המוסמכים ב{COUNTRY_HE} סמכות שיפוט, בלי לפגוע בהגנות צרכן קוגנטיות במקום מגוריכם.</p>

<h2>11. יצירת קשר</h2>
<p>השתמשו ב<a href="/vidsum/takedown">טופס יצירת הקשר וההסרה</a>.</p>
""",
}

PRIVACY = {
    "en": f"""
<h1>Privacy policy</h1>
<p class="eff">Effective {EFFECTIVE}. Draft, pending legal review.</p>

<h2>Who we are</h2>
<p>Pawed ({SITE}) is operated by {OPERATOR}, {COUNTRY}, who is the controller of the personal data described here. To contact us about privacy use the <a href="/vidsum/takedown">request form</a> and choose "Privacy".</p>

<h2>What Pawed does with data</h2>
<p>Pawed summarises publicly available podcasts and videos. That processing concerns the episodes, not your personal content. This page explains what we know about <b>you</b> as a visitor or account holder.</p>

<h2>What we collect</h2>
<ul>
<li><b>When you visit:</b> your IP address and basic request details (browser, pages) are handled by our hosting and security providers to deliver and protect the site. We use the country that your IP address maps to, at the moment of the request, to choose your default language and which content to show. We do not save it with your profile.</li>
<li><b>If you sign in with Google:</b> your Google account ID, name, email address and profile picture link. We never receive your Google password.</li>
<li><b>Your choices and activity:</b> languages, preferred listening platform, sources you add or hide, episodes you submit, thumbs up or down ratings, and whether your name is hidden.</li>
<li><b>Cookies and local storage:</b> a session cookie that keeps you signed in, a language cookie (pawed_lang), and a small browser flag that remembers a dismissed hint. These are needed for the site to work.</li>
<li><b>Analytics:</b> Pawed uses Google Analytics 4. It sets cookies and collects usage data such as pages viewed, device type, approximate location and referrer, so we can understand how the site is used. If you are in the EU, the UK or Switzerland, analytics loads only after you click Accept in the banner, and you can <a href="#" class="cc">reset your choice</a> at any time. See Google's own policy for how it handles that data.</li>
</ul>

<h2>What we do not do</h2>
<p>We do not sell personal data. We show no advertising and do not build advertising profiles.</p>

<h2>Why we use data (legal bases)</h2>
<p>To run your account and the features you ask for (performing our service); to keep the site secure and working (legitimate interest); to measure usage (consent or legitimate interest, depending on where you live); and to meet legal duties.</p>

<h2>Who else processes data</h2>
<ul>
<li><b>Google:</b> sign-in, Analytics, and AI models (Gemini) used to write and translate summaries from public episode text. No account data is sent to the AI models.</li>
<li><b>Cloudflare:</b> network, caching and security. <b>Render:</b> hosting, in the United States. <b>Hostinger:</b> domain name service.</li>
<li><b>AI and transcript providers</b> (for example LunaRoute and Supadata): process public episode content to produce transcripts and summaries.</li>
<li><b>Content hosts:</b> thumbnails and podcast artwork load from YouTube, Google and podcast hosts, so they see your IP address when your browser fetches them. Links to Spotify, Apple Podcasts, YouTube and podcast sites leave Pawed and follow their own policies.</li>
</ul>
<p>Data is therefore processed outside your country, including in the United States. Where required we rely on lawful transfer mechanisms.</p>

<h2>How long we keep it</h2>
<p>Account data, preferences and ratings are kept until you ask us to delete them or you delete your account. Server logs are kept for a short period. Analytics follow Google's retention settings.</p>

<h2>Your rights</h2>
<p>Depending on where you live (for example under the GDPR, UK GDPR, California law or Israel's Privacy Protection Law) you may have the right to access, correct, delete or export your data, to object to or restrict some processing, to withdraw consent, and to complain to your data protection authority (in Israel, the Privacy Protection Authority). Use the <a href="/vidsum/takedown">request form</a>. We aim to answer within 30 days.</p>

<h2>People mentioned in summaries</h2>
<p>Summaries mention people who speak on, or are discussed in, public shows. If a summary about you is inaccurate or you want it removed, use the same form and choose "Inaccurate or harmful statement" or "Privacy".</p>

<h2>Children</h2>
<p>Pawed is not directed to children under 16 and we do not knowingly collect their data.</p>

<h2>Security</h2>
<p>We use reasonable technical measures, but no online service is perfectly secure.</p>

<h2>Changes</h2>
<p>We may update this policy and its date. For material changes we will make the update visible on the site.</p>
""",
    "he": f"""
<h1>מדיניות פרטיות</h1>
<p class="eff">בתוקף מ-{EFFECTIVE_HE}. טיוטה, בכפוף לבדיקה משפטית.</p>

<h2>מי אנחנו</h2>
<p>Pawed ({SITE}) מופעל על ידי {OPERATOR_HE}, {COUNTRY_HE}, שהוא בעל מאגר המידע האישי המתואר כאן. ליצירת קשר בנושא פרטיות השתמשו ב<a href="/vidsum/takedown">טופס הפניות</a> ובחרו "פרטיות".</p>

<h2>מה Pawed עושה עם מידע</h2>
<p>Pawed מסכם פודקאסטים וסרטונים זמינים לציבור. העיבוד הזה נוגע לפרקים ולא לתוכן האישי שלכם. הדף הזה מסביר מה אנחנו יודעים עליכם כמבקרים או כבעלי חשבון.</p>

<h2>מה אנחנו אוספים</h2>
<ul>
<li><b>בעת ביקור:</b> כתובת ה-IP ופרטי בקשה בסיסיים (דפדפן, דפים) מטופלים על ידי ספקי האחסון והאבטחה שלנו כדי להעביר ולהגן על האתר. אנו משתמשים במדינה שכתובת ה-IP שלכם מתאימה לה, ברגע הבקשה, כדי לבחור שפת ברירת מחדל ואילו תכנים להציג. איננו שומרים אותה בפרופיל שלכם.</li>
<li><b>אם נכנסתם עם Google:</b> מזהה חשבון Google, שם, כתובת דוא"ל וקישור לתמונת הפרופיל. איננו מקבלים את הסיסמה שלכם ל-Google.</li>
<li><b>הבחירות והפעילות שלכם:</b> שפות, פלטפורמת האזנה מועדפת, מקורות שהוספתם או הסתרתם, פרקים שהגשתם, דירוגי אגודל למעלה או למטה, והאם שמכם מוסתר.</li>
<li><b>עוגיות ואחסון מקומי:</b> עוגיית התחברות ששומרת אתכם מחוברים, עוגיית שפה (pawed_lang), ודגל קטן בדפדפן שזוכר רמז שנסגר. אלה נדרשים לתפקוד האתר.</li>
<li><b>אנליטיקה:</b> Pawed משתמש ב-Google Analytics 4. הוא מציב עוגיות ואוסף נתוני שימוש כמו דפים שנצפו, סוג מכשיר, מיקום משוער ומקור הגעה, כדי שנבין איך משתמשים באתר. אם אתם באיחוד האירופי, בבריטניה או בשווייץ, האנליטיקה נטענת רק לאחר שלחצתם על אישור בבאנר, ואפשר <a href="#" class="cc">לאפס את הבחירה</a> בכל עת. ראו את מדיניות Google לגבי הטיפול בנתונים אלה.</li>
</ul>

<h2>מה אנחנו לא עושים</h2>
<p>איננו מוכרים מידע אישי. איננו מציגים פרסומות ואיננו בונים פרופילים פרסומיים.</p>

<h2>למה אנחנו משתמשים במידע (בסיסים משפטיים)</h2>
<p>כדי להפעיל את החשבון והתכונות שביקשתם (מתן השירות); כדי לשמור על אבטחת האתר ותקינותו (אינטרס לגיטימי); כדי למדוד שימוש (הסכמה או אינטרס לגיטימי, בהתאם למקום מגוריכם); וכדי לעמוד בחובות חוקיות.</p>

<h2>מי עוד מעבד מידע</h2>
<ul>
<li><b>Google:</b> כניסה, Analytics ומודלי בינה מלאכותית (Gemini) שמשמשים לכתיבה ותרגום של סיכומים מתוך טקסט פרקים ציבוריים. לא נשלח למודלים מידע על חשבונות.</li>
<li><b>Cloudflare:</b> רשת, מטמון ואבטחה. <b>Render:</b> אחסון, בארצות הברית. <b>Hostinger:</b> שירות שמות דומיין.</li>
<li><b>ספקי בינה מלאכותית ותמלול</b> (למשל LunaRoute ו-Supadata): מעבדים תוכן פרקים ציבורי כדי להפיק תמלולים וסיכומים.</li>
<li><b>מארחי תוכן:</b> תמונות ממוזערות ועטיפות פודקאסט נטענות מ-YouTube, Google ומארחי פודקאסטים, ולכן הם רואים את כתובת ה-IP שלכם כשהדפדפן מביא אותן. קישורים ל-Spotify, Apple Podcasts, YouTube ואתרי פודקאסטים יוצאים מ-Pawed ופועלים לפי המדיניות שלהם.</li>
</ul>
<p>לכן מידע מעובד מחוץ למדינתכם, כולל בארצות הברית. כאשר נדרש, אנו נשענים על מנגנוני העברה חוקיים.</p>

<h2>כמה זמן אנחנו שומרים</h2>
<p>נתוני חשבון, העדפות ודירוגים נשמרים עד שתבקשו למחוק אותם או תמחקו את החשבון. יומני שרת נשמרים לתקופה קצרה. האנליטיקה פועלת לפי הגדרות השמירה של Google.</p>

<h2>הזכויות שלכם</h2>
<p>בהתאם למקום מגוריכם (למשל לפי ה-GDPR, ה-GDPR הבריטי, החוק בקליפורניה או חוק הגנת הפרטיות הישראלי) ייתכן שיש לכם זכות לעיין במידע, לתקן, למחוק או לייצא אותו, להתנגד לעיבוד מסוים או להגביל אותו, לבטל הסכמה, ולהגיש תלונה לרשות להגנת המידע (בישראל, הרשות להגנת הפרטיות). השתמשו ב<a href="/vidsum/takedown">טופס הפניות</a>. אנו שואפים להשיב בתוך 30 יום.</p>

<h2>אנשים שמוזכרים בסיכומים</h2>
<p>הסיכומים מזכירים אנשים שמדברים בתוכניות ציבוריות או שמדברים עליהם בהן. אם סיכום עליכם אינו מדויק או שאתם רוצים להסירו, השתמשו באותו טופס ובחרו "קביעה לא מדויקת או פוגענית" או "פרטיות".</p>

<h2>ילדים</h2>
<p>Pawed אינו מיועד לילדים מתחת לגיל 16 ואיננו אוספים ביודעין מידע עליהם.</p>

<h2>אבטחה</h2>
<p>אנו נוקטים אמצעים טכניים סבירים, אך אין שירות מקוון בטוח לחלוטין.</p>

<h2>שינויים</h2>
<p>אנו רשאים לעדכן את המדיניות ואת תאריכה. בשינויים מהותיים נציג את העדכון באתר.</p>
""",
}

FORM = {
    "en": dict(
        title="Takedown, correction and data requests",
        intro=f"Use this form if you own rights in content shown on Pawed, run a show and want it removed, found an inaccurate or harmful statement, or want to access or delete your personal data. We aim to reply within {RESPONSE_DAYS} days, and copyright notices as fast as we can. Requests are reviewed by a person.",
        type_l="What is this about?", name_l="Your full name", email_l="Your email (we reply here)", org_l="Organisation or show (optional)",
        role_l="You are", roles=["The rights holder", "Authorised to act for the rights holder", "The person mentioned", "The show owner or producer", "Someone else"],
        urls_l="Link(s) to the Pawed page(s) concerned", urls_h="One per line, for example https://pawed.io/vidsum/article/...",
        work_l="The original work (copyright notices only)", work_h="Name of the episode or work and where it is published",
        details_l="What should we do, and why?", details_h="Be as specific as you can: which text, image or statement, and what is wrong or what you want changed.",
        good="I believe in good faith that the use described above is not authorised by the rights holder, its agent or the law, or that the statement I describe is inaccurate.",
        acc="The information in this request is accurate, and for a copyright notice I am the rights holder or authorised to act for them.",
        sig_l="Signature (type your full name)", send="Send request", sending="Sending…",
        ok="Received. Your reference is", ok2="Keep it if you contact us again.", err="Something went wrong. Please check the fields and try again.",
        legal=f"Knowingly sending a false notice can have legal consequences. We use what you send only to handle your request and keep it as long as needed for that purpose. See the <a href=\"/vidsum/privacy\">privacy policy</a>.",
    ),
    "he": dict(
        title="בקשות הסרה, תיקון ומידע אישי",
        intro=f"השתמשו בטופס זה אם אתם בעלי זכויות בתוכן המוצג ב-Pawed, מפעילים פודקאסט ורוצים להסירו, מצאתם קביעה לא מדויקת או פוגענית, או רוצים לעיין במידע האישי שלכם או למחוק אותו. אנו שואפים להשיב בתוך {RESPONSE_DAYS} ימים, והודעות זכויות יוצרים במהירות האפשרית. בקשות נבדקות על ידי אדם.",
        type_l="במה מדובר?", name_l="שם מלא", email_l="דוא\"ל (נשיב אליו)", org_l="ארגון או פודקאסט (אופציונלי)",
        role_l="אתם", roles=["בעל הזכויות", "מורשה לפעול בשם בעל הזכויות", "האדם המוזכר", "בעלים או מפיק של הפודקאסט", "אחר"],
        urls_l="קישור(ים) לדף ב-Pawed הנוגע לעניין", urls_h="אחד בכל שורה, למשל https://pawed.io/vidsum/article/...",
        work_l="היצירה המקורית (בהודעות זכויות יוצרים בלבד)", work_h="שם הפרק או היצירה והיכן היא מפורסמת",
        details_l="מה לעשות, ולמה?", details_h="פרטו ככל האפשר: איזה טקסט, תמונה או קביעה, ומה לא נכון או מה אתם רוצים לשנות.",
        good="אני מאמין בתום לב שהשימוש המתואר לעיל אינו מורשה על ידי בעל הזכויות, שלוחו או הדין, או שהקביעה שתיארתי אינה מדויקת.",
        acc="המידע בבקשה זו מדויק, ובהודעת זכויות יוצרים אני בעל הזכויות או מורשה לפעול בשמו.",
        sig_l="חתימה (הקלידו שם מלא)", send="שליחת הבקשה", sending="שולח…",
        ok="התקבל. מספר הפנייה שלכם הוא", ok2="שמרו אותו אם תפנו אלינו שוב.", err="משהו השתבש. בדקו את השדות ונסו שוב.",
        legal="שליחה ביודעין של הודעה כוזבת עלולה לגרור השלכות משפטיות. אנו משתמשים במה שתשלחו רק לטיפול בבקשה ושומרים אותו כל עוד נדרש למטרה זו. ראו את <a href=\"/vidsum/privacy\">מדיניות הפרטיות</a>.",
    ),
}

CSS = """
:root{--red:#e3222b;--ink:#222;--muted:#666;--line:#e3e3e3}
*{box-sizing:border-box}body{margin:0;font-family:-apple-system,"Segoe UI",Roboto,Arial,sans-serif;background:#f7f5fb;color:var(--ink);line-height:1.6}
.top{border-top:4px solid var(--red);background:#fff;border-bottom:1px solid var(--line)}
.top-in{max-width:820px;margin:auto;padding:12px 22px;display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}
.top img{height:44px;display:block}.top nav{display:flex;gap:16px;font-size:14px;flex-wrap:wrap}.top a{color:var(--ink);text-decoration:none;font-weight:700}.top a:hover{color:var(--red)}
.langsw{display:inline-flex;gap:8px}.langsw a{font-size:20px;opacity:.45;cursor:pointer;text-decoration:none}.langsw a.on{opacity:1}
main{max-width:820px;margin:26px auto 60px;padding:0 22px}
.card{background:#fff;border:1px solid var(--line);border-radius:12px;padding:26px 28px}
h1{font-size:30px;margin:0 0 4px}h2{font-size:18px;margin:26px 0 6px}p,li{font-size:15.5px}ul{padding-inline-start:22px}.eff{color:var(--muted);font-size:13px;margin:0 0 6px}
a{color:#1556d6}
label{display:block;font-weight:700;font-size:14px;margin:14px 0 4px}input,select,textarea{width:100%;font:inherit;padding:9px 11px;border:1px solid #ccc;border-radius:8px;background:#fff}
textarea{min-height:110px;resize:vertical}.chk{display:flex;gap:9px;align-items:flex-start;font-weight:400;margin:10px 0}.chk input{width:auto;margin-top:5px}
button.go{margin-top:16px;background:var(--red);color:#fff;border:0;border-radius:999px;padding:11px 26px;font:inherit;font-weight:800;cursor:pointer}button.go:disabled{opacity:.6}
.msg{margin-top:14px;font-weight:700}.msg.ok{color:#18723a}.msg.err{color:#b9141c}.small{color:var(--muted);font-size:12.5px;margin-top:14px}
.hp{position:absolute;left:-9999px;opacity:0}
footer{max-width:820px;margin:0 auto 40px;padding:0 22px;color:var(--muted);font-size:12.5px;text-align:center}
"""


def _page(title, body, lang, extra_js=""):
    he = lang == "he"
    nav = (f'<a href="/vidsum">{"ראשי" if he else "Home"}</a><a href="/vidsum/terms">{"תנאי שימוש" if he else "Terms"}</a>'
           f'<a href="/vidsum/privacy">{"פרטיות" if he else "Privacy"}</a><a href="/vidsum/takedown">{"הסרה ופניות" if he else "Takedown"}</a>')
    sw = ('<span class="langsw"><a data-l="en" class="%s" title="%s">\U0001F1FA\U0001F1F8</a><a data-l="he" class="%s" title="%s">\U0001F1EE\U0001F1F1</a></span>'
          % ("" if he else "on", "English", "on" if he else "", "עברית" if he else "Hebrew"))
    js = ("<script>document.querySelectorAll('.langsw a').forEach(function(a){a.onclick=function(e){e.preventDefault();var l=a.dataset.l;"
          "document.cookie='pawed_lang='+l+';path=/;max-age=31536000;samesite=lax';"
          "try{fetch('/api/vidsum/lang',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({lang:l})}).finally(function(){location.reload()});}"
          "catch(x){location.reload()}};});</script>")
    return (f'<!doctype html><html lang="{lang}" dir="{"rtl" if he else "ltr"}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{_html.escape(title)} | Pawed</title><meta name="robots" content="index,follow"><style>{CSS}</style></head><body>'
            f'<div class="top"><div class="top-in"><a href="/"><img src="/vidsum/pawed-wordmark.png" alt="Pawed"></a><nav>{nav}</nav>{sw}</div></div>'
            f'<main><div class="card">{body}</div></main>'
            f'<footer>Pawed · {SITE}</footer>{js}{extra_js}</body></html>')


def render_terms(lang):
    return _page("תנאי שימוש" if lang == "he" else "Terms of use", TERMS[lang], lang)


def render_privacy(lang):
    js = ("<script>document.querySelectorAll('a.cc').forEach(function(a){a.onclick=function(e){e.preventDefault();"
          "document.cookie='pawed_consent=;path=/;max-age=0;samesite=lax';location.reload()}});</script>")
    return _page("מדיניות פרטיות" if lang == "he" else "Privacy policy", PRIVACY[lang], lang, js)


def render_takedown(lang):
    f = FORM[lang]
    he = lang == "he"
    e = _html.escape
    kinds = "".join(f'<option value="{k}">{e(v[1] if he else v[0])}</option>' for k, v in KINDS.items())
    roles = "".join(f"<option>{e(r)}</option>" for r in f["roles"])
    body = (f'<h1>{e(f["title"])}</h1><p>{e(f["intro"])}</p>'
            f'<form id="tf" novalidate>'
            f'<label>{e(f["type_l"])}</label><select name="kind">{kinds}</select>'
            f'<label>{e(f["name_l"])}</label><input name="name" maxlength="120" required autocomplete="name">'
            f'<label>{e(f["email_l"])}</label><input name="email" type="email" maxlength="160" required autocomplete="email" dir="ltr">'
            f'<label>{e(f["org_l"])}</label><input name="org" maxlength="160">'
            f'<label>{e(f["role_l"])}</label><select name="role">{roles}</select>'
            f'<label>{e(f["urls_l"])}</label><textarea name="urls" maxlength="2000" placeholder="{e(f["urls_h"])}" dir="ltr" required></textarea>'
            f'<label>{e(f["work_l"])}</label><textarea name="work" maxlength="1500" placeholder="{e(f["work_h"])}"></textarea>'
            f'<label>{e(f["details_l"])}</label><textarea name="details" maxlength="4000" placeholder="{e(f["details_h"])}" required></textarea>'
            f'<label class="chk"><input type="checkbox" name="good" required><span>{e(f["good"])}</span></label>'
            f'<label class="chk"><input type="checkbox" name="acc" required><span>{e(f["acc"])}</span></label>'
            f'<label>{e(f["sig_l"])}</label><input name="signature" maxlength="120" required>'
            f'<input class="hp" name="website" tabindex="-1" autocomplete="off" aria-hidden="true">'
            f'<button class="go" type="submit">{e(f["send"])}</button><div class="msg" id="tmsg"></div>'
            f'<p class="small">{f["legal"]}</p></form>')
    js = ("<script>(function(){var T=%s,f=document.getElementById('tf'),m=document.getElementById('tmsg');"
          "f.onsubmit=function(ev){ev.preventDefault();var d={};new FormData(f).forEach(function(v,k){d[k]=v});d.good=f.good.checked;d.acc=f.acc.checked;d.lang=document.documentElement.lang;"
          "var b=f.querySelector('button');b.disabled=true;b.textContent=T.sending;m.className='msg';m.textContent='';"
          "fetch('/api/vidsum/takedown',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)}).then(function(r){return r.json()}).then(function(j){"
          "if(j.ok){m.className='msg ok';m.textContent=T.ok+' '+j.ref+'. '+T.ok2;f.reset();}else{m.className='msg err';m.textContent=j.error||T.err;}"
          "b.disabled=false;b.textContent=T.send}).catch(function(){m.className='msg err';m.textContent=T.err;b.disabled=false;b.textContent=T.send})};})();</script>"
          % json.dumps({k: f[k] for k in ("sending", "send", "ok", "ok2", "err")}, ensure_ascii=False))
    return _page(f["title"], body, lang, js)


# ------------------------------------------------------------------ takedown requests: storage + rate limit
_RATE = {}
_RATE_LOCK = threading.Lock()
_EMAIL = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,190}\.[^@\s]{2,}$")


def _db():
    c = multiuser.db()
    c.execute("CREATE TABLE IF NOT EXISTS takedown_requests(id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, ref TEXT, kind TEXT, name TEXT, email TEXT, org TEXT, "
              "role TEXT, urls TEXT, work TEXT, details TEXT, signature TEXT, lang TEXT, status TEXT DEFAULT 'new', note TEXT DEFAULT '')")
    return c


def _limited(ip):
    """5 requests per hour per address"""
    now = time.time()
    with _RATE_LOCK:
        hits = [t for t in _RATE.get(ip, []) if now - t < 3600]
        if len(hits) >= 5:
            _RATE[ip] = hits
            return True
        hits.append(now)
        _RATE[ip] = hits
        return False


def submit(req, ip=""):
    """-> (ok, payload). Validates, stores, returns a reference number."""
    if (req.get("website") or "").strip():                 # honeypot: bots fill every field
        return True, {"ref": "T-0000"}
    if _limited(ip or "?"):
        return False, {"error": "Too many requests, please try again later."}
    g = lambda k, n: str(req.get(k) or "").strip()[:n]
    name, email, urls, details, sig = g("name", 120), g("email", 160), g("urls", 2000), g("details", 4000), g("signature", 120)
    kind = g("kind", 20) if g("kind", 20) in KINDS else "other"
    if not name or not _EMAIL.match(email) or not details or not sig:
        return False, {"error": "Please fill in your name, a valid email, the details and your signature."}
    if kind != "privacy" and not urls:
        return False, {"error": "Please add the link(s) to the Pawed page(s) concerned."}
    if not (req.get("good") is True and req.get("acc") is True):
        return False, {"error": "Please tick both statements."}
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    with _db() as c:
        cur = c.execute("INSERT INTO takedown_requests(ts,kind,name,email,org,role,urls,work,details,signature,lang) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                        (ts, kind, name, email, g("org", 160), g("role", 80), urls, g("work", 1500), details, sig, g("lang", 5)))
        ref = "T-%05d" % cur.lastrowid
        c.execute("UPDATE takedown_requests SET ref=? WHERE id=?", (ref, cur.lastrowid))
    try:
        multiuser.log(f"takedown request {ref} ({kind}) from {email}: {details[:120]}")
    except Exception:
        pass
    return True, {"ref": ref}


def list_requests(limit=100):
    with _db() as c:
        return [dict(r) for r in c.execute("SELECT * FROM takedown_requests ORDER BY id DESC LIMIT ?", (limit,)).fetchall()]
