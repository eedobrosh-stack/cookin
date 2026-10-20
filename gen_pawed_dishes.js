// Builds assets/pawed_dishes.json (the Pawed "מבשלים" section reads it): every cookin dish with the fields the cards need.
// Re-run after cookin syncs new dishes:  node gen_pawed_dishes.js
const fs = require("fs"), vm = require("vm");
const ctx = { console, window: {} }; vm.createContext(ctx);
const files = ["data.js", ...Array.from({ length: 10 }, (_, i) => "data" + (i + 2) + ".js")];
for (const f of files) vm.runInContext(fs.readFileSync("site/" + f, "utf8"), ctx);
const R = vm.runInContext("RECIPES", ctx);
const page = vm.runInContext(fs.readFileSync("site/dishlinks.js", "utf8") + ";DISH_PAGE", ctx);
const group = r => r.category === "בקר" ? "beef" : r.category === "עוף" ? "chicken" : (r.diet === "דגים" || r.category === "דגים") ? "fish" : r.diet === "צמחוני" ? "veg" : null;
const out = R.filter(r => r.image && page[String(r.id)] && group(r)).map(r => ({
  id: String(r.id), name: r.name.replace(/\s*\p{Extended_Pictographic}️?/gu, "").trim(), group: group(r), category: r.category, diet: r.diet,
  image: r.image, time: r.time || "", serves: r.serves || "", creator: r.creator || "",
  intro: (r.intro || "").replace(/\s+/g, " ").slice(0, 150), url: "https://cookin.jarcud.com/" + page[String(r.id)] }));
fs.writeFileSync("assets/pawed_dishes.json", JSON.stringify({ total: R.length, dishes: out }));
const c = {}; out.forEach(d => c[d.group] = (c[d.group] || 0) + 1);
console.log(R.length, "dishes,", out.length, "usable", c);
