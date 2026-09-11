// Gluten-free filter (added 2026-09-07). Shared by index.html + en.html.
// A dish is gluten-free when none of its `needs` keys is a hard-gluten ingredient
// and it is not manually excluded. Pasta / soy-based sauces are ALLOWED — GF users
// swap in gluten-free pasta / tamari; the UI shows a note when the filter is on.
const GLUTEN_KEYS = new Set(["flour","breadcrumbs","semolina","noodles","dumplings","bread","ravioli"]);
const GLUTEN_EXCLUDE_IDS = new Set([
  "68238", // סאטה של ג'ירף — served on schnitzel (breaded)
]);
const GF_SWAP_KEYS = new Set(["pasta","soy","teriyaki","hoisin","oyster-sauce","worcester"]);
function isGlutenFree(r){
  if(GLUTEN_EXCLUDE_IDS.has(String(r.id))) return false;
  return !(r.needs||[]).some(k => GLUTEN_KEYS.has(k));
}
function gfNeedsSwap(r){ return (r.needs||[]).some(k => GF_SWAP_KEYS.has(k)); }
