// Diet filters (added 2026-09-24). Shared by index.html + en.html; sits next to gf.js.
// Vegetarian = the dish's diet field. Vegan = vegetarian AND none of its `needs` keys is an
// animal product. Stock / honey-silan / noodles are ALLOWED (swap to vegetable stock, silan or
// maple, egg-free noodles); the UI shows a note when the vegan filter is on.
const VEGETARIAN_DIETS = new Set(["צמחוני","Vegetarian"]);
const NON_VEGAN_KEYS = new Set(["butter","cream","milk","cream-cheese","parmesan","mozzarella","burrata","greek-yogurt",
  "sour-cream","feta","ricotta","pecorino","mascarpone","eggs","ravioli","dumplings","fish-sauce","oyster-sauce","dashi",
  "anchovy","shrimp","worcester","hoisin"]);
const VEGAN_EXCLUDE_IDS = new Set([]);
const VEGAN_SWAP_KEYS = new Set(["stock","honey-silan","noodles"]);
function isVegetarian(r){ return VEGETARIAN_DIETS.has(r.diet); }
function isVegan(r){
  if(!isVegetarian(r) || VEGAN_EXCLUDE_IDS.has(String(r.id))) return false;
  return !(r.needs||[]).some(k => NON_VEGAN_KEYS.has(k));
}
function veganNeedsSwap(r){ return (r.needs||[]).some(k => VEGAN_SWAP_KEYS.has(k)); }
