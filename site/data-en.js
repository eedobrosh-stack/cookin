/* Cookin — recipe data, English edition (generated from the WhatsApp "cookin" group, 2026-08-11) */

const INGREDIENTS = {
  /* Proteins */
  chicken:      {label:"Chicken / chicken thighs", group:"Proteins", subs:["beef"]},
  beef:         {label:"Beef (asado/brisket/sirloin)", group:"Proteins", subs:["chicken"]},
  bacon:        {label:"Bacon (or goose bacon)", group:"Proteins", subs:[]},
  "fish-white": {label:"White fish (sea bass/bream/cod)", group:"Proteins", subs:["salmon"]},
  salmon:       {label:"Salmon", group:"Proteins", subs:["fish-white"]},
  tuna:         {label:"Canned tuna in oil", group:"Proteins", subs:["anchovy"]},
  anchovy:      {label:"Anchovies", group:"Proteins", subs:["tuna"]},
  tofu:         {label:"Tofu", group:"Proteins", subs:["chicken"]},
  /* Dairy */
  butter:       {label:"Butter", group:"Dairy", subs:[]},
  cream:        {label:"Heavy cream", group:"Dairy", subs:["coconut-milk","milk"]},
  milk:         {label:"Milk", group:"Dairy", subs:["cream"]},
  "cream-cheese":{label:"Cream cheese", group:"Dairy", subs:["cream"]},
  parmesan:     {label:"Parmesan / hard cheese", group:"Dairy", subs:[]},
  /* Vegetables & Fruit */
  garlic:       {label:"Garlic", group:"Vegetables & Fruit", subs:[]},
  onion:        {label:"Onion", group:"Vegetables & Fruit", subs:["red-onion","leek"]},
  "red-onion":  {label:"Red onion", group:"Vegetables & Fruit", subs:["onion"]},
  scallion:     {label:"Scallions", group:"Vegetables & Fruit", subs:["leek"]},
  leek:         {label:"Leek", group:"Vegetables & Fruit", subs:["onion","scallion"]},
  lemon:        {label:"Lemon", group:"Vegetables & Fruit", subs:["lime"]},
  lime:         {label:"Lime", group:"Vegetables & Fruit", subs:["lemon"]},
  orange:       {label:"Orange", group:"Vegetables & Fruit", subs:[]},
  "tomatoes-fresh":{label:"Fresh tomatoes", group:"Vegetables & Fruit", subs:["cherry-tomatoes"]},
  "cherry-tomatoes":{label:"Cherry tomatoes", group:"Vegetables & Fruit", subs:["tomatoes-fresh"]},
  "pepper-red": {label:"Red bell pepper", group:"Vegetables & Fruit", subs:["capsicum-roasted"]},
  "capsicum-roasted":{label:"Roasted pepper", group:"Vegetables & Fruit", subs:["pepper-red"]},
  chili:        {label:"Chili / hot pepper", group:"Vegetables & Fruit", subs:[]},
  ginger:       {label:"Fresh ginger", group:"Vegetables & Fruit", subs:[]},
  mushrooms:    {label:"Mushrooms", group:"Vegetables & Fruit", subs:[]},
  broccoli:     {label:"Broccoli", group:"Vegetables & Fruit", subs:[]},
  "bok-choy":   {label:"Bok choy", group:"Vegetables & Fruit", subs:["cabbage-napa"]},
  "snow-peas":  {label:"Snow peas", group:"Vegetables & Fruit", subs:[]},
  fennel:       {label:"Fennel", group:"Vegetables & Fruit", subs:[]},
  "cabbage-napa":{label:"Napa cabbage", group:"Vegetables & Fruit", subs:["bok-choy"]},
  zucchini:     {label:"Zucchini", group:"Vegetables & Fruit", subs:[]},
  potato:       {label:"Potatoes", group:"Vegetables & Fruit", subs:[]},
  grapes:       {label:"Grapes", group:"Vegetables & Fruit", subs:[]},
  cucumbers:    {label:"Cucumbers (small)", group:"Vegetables & Fruit", subs:[]},
  spinach:      {label:"Spinach / baby greens", group:"Vegetables & Fruit", subs:[]},
  /* Herbs */
  basil:        {label:"Basil", group:"Herbs", subs:["parsley"]},
  parsley:      {label:"Parsley", group:"Herbs", subs:["coriander"]},
  coriander:    {label:"Cilantro", group:"Herbs", subs:["parsley"]},
  dill:         {label:"Dill", group:"Herbs", subs:[]},
  thyme:        {label:"Thyme", group:"Herbs", subs:[]},
  lemongrass:   {label:"Lemongrass", group:"Herbs", subs:[]},
  /* Pantry & Canned */
  pasta:        {label:"Pasta / spaghetti", group:"Pantry & Canned", subs:[]},
  rice:         {label:"Rice", group:"Pantry & Canned", subs:[]},
  "canned-tomatoes":{label:"Crushed tomatoes (canned)", group:"Pantry & Canned", subs:["tomatoes-fresh"]},
  "tomato-paste":{label:"Tomato paste", group:"Pantry & Canned", subs:[]},
  "pine-nuts":  {label:"Pine nuts", group:"Pantry & Canned", subs:[]},
  peanuts:      {label:"Peanuts", group:"Pantry & Canned", subs:[]},
  olives:       {label:"Olives (Kalamata)", group:"Pantry & Canned", subs:[]},
  capers:       {label:"Capers", group:"Pantry & Canned", subs:["olives"]},
  "honey-silan":{label:"Honey / date syrup / maple", group:"Pantry & Canned", subs:[]},
  mustard:      {label:"Mustard", group:"Pantry & Canned", subs:[]},
  vinegar:      {label:"Vinegar (wine/apple cider)", group:"Pantry & Canned", subs:[]},
  "wine-white": {label:"White wine / mirin", group:"Pantry & Canned", subs:[]},
  stock:        {label:"Stock / bouillon powder", group:"Pantry & Canned", subs:[]},
  cornflour:    {label:"Cornstarch", group:"Pantry & Canned", subs:[]},
  "coconut-milk":{label:"Coconut cream / coconut milk", group:"Pantry & Canned", subs:["cream"]},
  /* Asian */
  soy:          {label:"Soy sauce", group:"Asian Pantry", subs:[]},
  "fish-sauce": {label:"Fish sauce", group:"Asian Pantry", subs:["soy"]},
  hoisin:       {label:"Hoisin / oyster / mushroom sauce", group:"Asian Pantry", subs:["teriyaki"]},
  teriyaki:     {label:"Teriyaki sauce", group:"Asian Pantry", subs:["hoisin"]},
  gochujang:    {label:"Gochujang", group:"Asian Pantry", subs:["chili-crisp"]},
  "chili-crisp":{label:"Chili oil / chili crisp", group:"Asian Pantry", subs:["chili"]},
  "sesame-oil": {label:"Sesame oil", group:"Asian Pantry", subs:[]},
  "curry-red":  {label:"Red curry paste", group:"Asian Pantry", subs:[]},
  dashi:        {label:"Dashi powder", group:"Asian Pantry", subs:[]},
  miso:         {label:"Miso paste", group:"Asian Pantry", subs:[]},
  wakame:       {label:"Wakame seaweed", group:"Asian Pantry", subs:[]},
  jujube:       {label:"Jujube (Chinese date)", group:"Asian Pantry", subs:[]},
  ginseng:      {label:"Ginseng root", group:"Asian Pantry", subs:[]},
  "kaffir":     {label:"Kaffir lime leaves", group:"Asian Pantry", subs:[]},
  /* basics — not shown in the picker */
  salt:{label:"Salt",basic:true}, pepper:{label:"Black pepper",basic:true},
  oil:{label:"Oil",basic:true}, "olive-oil":{label:"Olive oil",basic:true},
  sugar:{label:"Sugar",basic:true}, flour:{label:"Flour",basic:true},
  spices:{label:"Dried spices",basic:true}, water:{label:"Water",basic:true},
  "baking-powder":{label:"Baking powder / baking soda",basic:true}
};

const RECIPES = [
{
  id:"8740", diet:"Vegetarian", image:"8740.jpg", category:"Pasta",
  name:"Lemon Butter Pasta with Pine Nuts & Basil",
  searchAlias:"פסטה בחמאת לימון, צנוברים ובזיליקום",
  creator:"Dor Peleg", time:"25 min", serves:"Serves 4",
  video:"https://www.facebook.com/reel/1737078344368899",
  intro:"The restaurant secret: add the pasta water first, then the butter — that's how you get an emulsion that makes the sauce silky and creamy.",
  needs:["pasta","garlic","butter","lemon","basil","pine-nuts","parmesan"],
  ingredientLines:[
    {text:"250 g dried pasta of your choice"},
    {text:"2-3 tbsp olive oil"},
    {text:"2-3 garlic cloves, thinly sliced"},
    {text:"200 g butter, cut into cubes"},
    {text:"Zest of 1 lemon"},
    {text:"Handful of basil leaves, finely chopped"},
    {text:"50 g toasted pine nuts"},
    {text:"Salt and black pepper"},
    {text:"To serve — grated Parmesan"}
  ],
  steps:[
    "Bring a pot of water to a boil, and once it's boiling, salt it generously. Add the pasta and stir so it doesn't stick.",
    "In a skillet over medium heat, warm the olive oil with the garlic and cook for a minute or two. Carefully add a ladle of the pasta water — then the butter cubes.",
    "Stir until the butter melts in and the sauce comes together. Add the lemon zest and basil, and season gently with black pepper and a little salt (the pasta water is already salty).",
    "When the pasta is almost done, transfer it to the sauce and cook another 3-4 minutes to reduce, stirring as you go. Add the pine nuts, toss, and serve hot with plenty of Parmesan."
  ],
  tips:"Careful not to burn the garlic — several commenters noted that frying it too long makes it bitter."
},
{
  id:"8891", diet:"Vegetarian", image:"8891.jpg", category:"Pasta",
  name:"Creamy Chili Crisp Pasta",
  searchAlias:"פסטה קרמית עם שמן צ'ילי (צ'ילי קריספ)",
  creator:"Chhaya Joshi", time:"25 min", serves:"Serves 4",
  video:"https://www.facebook.com/reel/1233367215603154",
  needs:["pasta","butter","cream-cheese","milk","cream","parmesan","chili-crisp","parsley"],
  ingredientLines:[
    {text:"340 g pasta (half a package)"},
    {text:"2 tbsp butter"},
    {text:"2 tbsp flour"},
    {text:"115 g cream cheese, softened"},
    {text:"2 cups milk"},
    {text:"3/4 cup heavy cream"},
    {text:"3/4 cup grated Parmesan"},
    {text:"1 tsp salt + 1 tsp garlic powder (optional: a pinch of turmeric for color — just a tiny bit!)"},
    {text:"1/4 cup chili oil / chili crisp"},
    {text:"Parsley for garnish"}
  ],
  steps:[
    "Cook the pasta al dente (a minute or two less than the package says — it will keep cooking in the sauce). Reserve a bit of the cooking water.",
    "In a skillet, melt the butter with the flour and stir until lightly golden, a minute or two over medium-low heat.",
    "Whisking constantly, gradually add the milk.",
    "Add the cream, Parmesan, cream cheese, salt, and garlic powder.",
    "Let the sauce simmer and thicken.",
    "Once the sauce is ready — stir in the chili oil.",
    "Add the pasta and toss gently until everything is coated. If it's too thick, loosen with pasta water.",
    "Serve immediately with parsley and another drizzle of chili oil."
  ],
  tips:"The most-loved comment (209 likes): swap the cream cheese for a tub of garlic-herb Boursin. No chili crisp? Chili flakes or hot sauce work."
},
{
  id:"9048", diet:"Vegetarian", image:"9048.jpg", category:"Soups & Sauces",
  name:"Red Chimichurri",
  searchAlias:"צ'ימיצ'ורי אדום",
  creator:"Vilde Olsen", time:"10 min",
  video:"https://www.facebook.com/reel/814920217525095",
  intro:"A fresh, punchy sauce for grilled meats — a red version with roasted pepper and red onion.",
  needs:["parsley","coriander","garlic","chili","capsicum-roasted","red-onion","vinegar","lime"],
  ingredientLines:[
    {text:"1 bunch fresh parsley"},
    {text:"1 bunch fresh cilantro"},
    {text:"2 garlic cloves, grated"},
    {text:"1 red chili"},
    {text:"1 roasted red pepper"},
    {text:"1/2 red onion"},
    {text:"1 tbsp smoked paprika"},
    {text:"1 tbsp dried oregano"},
    {text:"100 ml olive oil"},
    {text:"50 ml red wine vinegar"},
    {text:"Lime juice"},
    {text:"Salt and pepper to taste"}
  ],
  steps:[
    "Finely chop the parsley, cilantro, chili, roasted pepper, and red onion.",
    "Grate in the garlic and mix everything in a bowl.",
    "Add the smoked paprika and oregano, olive oil, vinegar, and lime juice.",
    "Season with salt and pepper, taste, and adjust. Best to let the sauce rest for half an hour before serving."
  ]
},
{
  id:"9205", diet:"Vegetarian", image:"9205.jpg", category:"Pasta",
  name:"Chili Lemon Butter Pasta",
  searchAlias:"פסטה בחמאת לימון צ'ילי",
  creator:"Coral Hota", time:"25 min", serves:"Serves 4-5",
  video:"https://www.facebook.com/reel/1296280915967572",
  intro:"Spicy, tangy, salty — a winning dish for company. Take care with the gentle emulsion of the cold butter.",
  needs:["pasta","garlic","lemon","chili","butter","parsley"],
  ingredientLines:[
    {text:"1 package linguine (500 g)"},
    {text:"1/4 cup olive oil"},
    {text:"6 garlic cloves, crushed"},
    {text:"Zest of 2 lemons"},
    {text:"Juice of 2 lemons"},
    {text:"1 tbsp crushed chili + 3-4 dried chilies (optional)"},
    {text:"1 tsp salt"},
    {text:"Handful of fresh za'atar/oregano leaves (optional)"},
    {text:"Handful of finely chopped parsley"},
    {text:"1 cup of the pasta cooking water"},
    {text:"200 g cold butter, cut into cubes"}
  ],
  steps:[
    "Bring a pot of water to a boil with 2 tbsp salt and cook the pasta with a timer per the package instructions.",
    "Meanwhile, in a skillet: heat the olive oil, add the garlic, lemon zest, and chili and stir. Add the lemon juice (over fairly high heat).",
    "Add a cup of the pasta water + salt + the za'atar/oregano leaves, and let it bubble.",
    "Turn off the heat and start adding the cold butter cubes, gently swirling the pan to build an emulsion. Too much heat at this stage will break the sauce.",
    "Add the drained pasta and the parsley with the heat off or on very low.",
    "Toss, taste, and adjust the seasoning. Your perfect pasta is ready."
  ],
  tips:"From the comments: any herb works here — fresh za'atar is especially recommended."
},
{
  id:"9354", diet:"Meat", image:"9354.jpg", category:"Chicken",
  name:"Coconut Lime Braised Chicken",
  searchAlias:"עוף מבושל בקוקוס וליים",
  creator:"Thegoodbite", time:"45 min", serves:"Serves 4 (630 calories, 34 g protein)",
  video:"https://www.facebook.com/reel/984185104477800",
  intro:"Golden boneless thighs simmer in a silky, rich, aromatic coconut-lime sauce.",
  needs:["chicken","coconut-milk","lime","garlic","ginger","onion","soy","honey-silan","coriander","stock"],
  ingredientLines:[
    {text:"8 boneless chicken thighs"},
    {text:"Coconut oil for searing"},
    {text:"Smoked paprika, salt, and pepper (to coat the chicken)"},
    {text:"1 shallot, finely chopped"},
    {text:"Grated garlic + grated ginger"},
    {text:"1 can coconut milk"},
    {text:"Chicken stock"},
    {text:"Soy sauce + honey"},
    {text:"Zest and juice of a whole lime"},
    {text:"Chopped cilantro + sliced almonds for garnish"},
    {text:"To serve: rice and a quick-pickled cucumber salad (rice vinegar, lime, soy, sesame oil, honey)"}
  ],
  steps:[
    "Coat the chicken thighs with smoked paprika, salt, and pepper.",
    "Sear in coconut oil in a hot pan until golden on both sides, then remove.",
    "In the same pan, sauté the shallot with the grated garlic and ginger.",
    "Add the coconut milk, stock, soy, honey, and plenty of lime zest and juice — stir into a silky sauce.",
    "Return the chicken and simmer gently for 10-12 minutes until cooked through. Finish with cilantro and lime.",
    "Serve over rice with the pickled cucumber salad and sliced almonds. (Recipe reconstructed from the video — exact quantities are in the creator's app.)"
  ]
},
{
  id:"9510", diet:"Meat", image:"9510.jpg", category:"Chicken",
  name:"The Afghan Dish — Chicken & Bacon in a Wok",
  searchAlias:"המנה האפגנית — פרגית ובייקון בווק",
  creator:"דנה רייכר", time:"45 min + marinating", serves:"Serves 4",
  video:"https://www.facebook.com/reel/1664771871444024",
  intro:"One of Dana Reicher's oldest and simplest recipes. Regular bacon for the original version, or goose bacon for a kosher one.",
  needs:["chicken","bacon","soy","peanuts","leek","wine-white","cornflour"],
  ingredientLines:[
    {text:"500 g boneless chicken thighs, cut into pieces"},
    {text:"100 g bacon, cut into rough cubes"},
    {group:"Marinade:"},
    {text:"1/4 cup soy sauce"},
    {text:"1 heaping tbsp sugar"},
    {group:"Stir-fry:"},
    {text:"1/3 cup fried peanuts"},
    {text:"1 leek stalk, sliced on the diagonal"},
    {text:"1/2 cup white wine / mirin"},
    {text:"1 heaping tsp cornstarch dissolved in 3 tbsp water"},
    {text:"3 tbsp soy sauce + 1 tbsp dark soy sauce"},
    {text:"2 tbsp sugar"}
  ],
  steps:[
    "Mix the chicken and bacon well with the soy-sugar marinade and marinate at least half an hour (overnight is fine).",
    "Heat a wok with oil and stir-fry the chicken and bacon with all the marinade until the meat is fully cooked.",
    "Add the white wine and bring to a boil. Add the leek and toss for a minute.",
    "Add both soy sauces and the sugar, stir-fry a minute or two, add the dissolved cornstarch, and bring back to a boil.",
    "Add the peanuts, stir, and turn off the heat.",
    "Serve alongside white rice with scallions and a generous scattering of crushed peanuts."
  ]
},
{
  id:"9675", diet:"Fish", image:"9675.jpg", category:"Fish",
  name:"Red Curry Poached Fish",
  searchAlias:"דג ברוטב קארי אדום (Red Curry Poached Fish)",
  creator:"Herman at Home", time:"30 min", serves:"Serves 4",
  video:"https://www.facebook.com/reel/1553289306225065",
  intro:"White fish gently poached in a red curry-coconut sauce you could simply drink.",
  needs:["fish-white","onion","garlic","ginger","curry-red","coconut-milk","fish-sauce","lime","coriander"],
  ingredientLines:[
    {text:"700 g white fish fillet (cod/sea bass/bream)"},
    {text:"1 tbsp neutral oil"},
    {text:"1 small white onion, chopped"},
    {text:"4 garlic cloves, crushed"},
    {text:"1 tbsp chopped fresh ginger"},
    {text:"3 tbsp red curry paste"},
    {text:"1 can (400 ml) full-fat coconut milk"},
    {text:"1 cup chicken or fish stock"},
    {text:"3 tbsp fish sauce"},
    {text:"1 tbsp sugar"},
    {text:"Juice of 1 lime"},
    {text:"Salt to taste"},
    {text:"For garnish: sliced red chili, cilantro, chili oil"}
  ],
  steps:[
    "Pat the fish dry with paper towels and season with salt on both sides.",
    "In a wide skillet, heat the oil and sauté the onion, garlic, and ginger for 1-2 minutes. Add the curry paste and fry 30 seconds to release the aroma.",
    "Add the coconut milk and stock, then the fish sauce, sugar, lime juice, and a pinch of salt. Bring to a slow, gentle simmer.",
    "Lay the fish gently into the bubbling sauce. Lower the heat and cook, covered, for 7-10 minutes until the fish is opaque and flakes easily.",
    "Transfer to plates, spoon the sauce over, and garnish with chili, cilantro, and chili oil. Serve with rice."
  ]
},
{
  id:"9833", diet:"Meat", image:"9833.jpg", category:"Chicken",
  name:"Juicy Chicken Thighs in a Mild Red Curry Sauce",
  searchAlias:"פרגית עסיסית ברוטב קארי אדום עדין",
  creator:"Dana Reicher Moyal", time:"60 min + marinating", serves:"Serves 4-5",
  video:"https://www.facebook.com/reel/1515976119934224",
  intro:"Perfect alongside mashed potatoes or rice. Fresh kaffir lime leaves take it to another level (they keep for months in the freezer).",
  needs:["chicken","garlic","soy","wine-white","ginger","curry-red","coconut-milk","kaffir","fish-sauce","broccoli","red-onion","zucchini","pepper-red","scallion"],
  ingredientLines:[
    {group:"Chicken & marinade:"},
    {text:"900 g boneless chicken thigh steaks"},
    {text:"1/2 tsp red curry paste"},
    {text:"2 garlic cloves, crushed"},
    {text:"2 tbsp soy sauce + 2 tbsp mirin + 2 tbsp oil"},
    {group:"Sauce:"},
    {text:"1 garlic clove, crushed"},
    {text:"1 tbsp grated fresh ginger"},
    {text:"1 heaping tbsp red curry paste"},
    {text:"1 can coconut cream"},
    {text:"2 fresh kaffir lime leaves"},
    {text:"1 tbsp sugar + 1 tsp fish sauce + a little salt"},
    {group:"Stir-fry:"},
    {text:"2 cups broccoli florets, blanched (2 min in boiling water)"},
    {text:"1 red onion, cut into quarters"},
    {text:"1 zucchini, sliced + 1 red bell pepper, cut into squares"},
    {text:"To top: handful of chopped scallions"}
  ],
  steps:[
    "Marinate the chicken for at least half an hour (overnight in the fridge is fine).",
    "Grill on a grill pan until nicely charred, then transfer to a 180°C (350°F) oven for about 7 minutes.",
    "Stir-fry the vegetables in a wide sauté pan: sear the onion over high heat, add the zucchini for light browning (keep it crisp), then the bell pepper and broccoli for just 20-30 seconds.",
    "Make the sauce: sauté the garlic and ginger, add the red curry paste, coconut cream, kaffir leaves, sugar, fish sauce, and salt. Reduce slightly.",
    "Bring it together: chicken and vegetables in the sauce, scatter with scallions, and serve with mashed potatoes or rice."
  ]
},
{
  id:"9992", diet:"Vegetarian", image:"9992.jpg", category:"Pasta",
  name:"The Cheapest Pasta You'll Ever Make ($2 Pasta)",
  searchAlias:"הפסטה הכי זולה שתכינו ($2 פסטה)",
  creator:"Thatdudecancook", time:"20 min",
  video:"https://www.facebook.com/reel/1478517650391045",
  intro:"Sonny Hurrell's minimalist lemon-pecorino pasta.",
  needs:["pasta","lemon","parmesan","butter"],
  ingredientLines:[
    {text:"280 g spaghetti"},
    {text:"Zest and juice of 2 lemons"},
    {text:"6 tbsp cold butter, cubed"},
    {text:"110 g mixed pecorino and Parmesan (or just one of them)"},
    {text:"Salt to taste"},
    {text:"Optional — lemon oil: 1/3 cup neutral oil blended with the peel of half a lemon, strained"},
    {text:"Optional: thinly sliced mint for garnish"}
  ],
  steps:[
    "(Optional) Lemon oil: blend the oil with the peel of half a lemon for about 45 seconds and strain through a fine sieve.",
    "Zest the lemons and squeeze the juice into the same bowl.",
    "Cook the spaghetti in moderately salted water (not too salty).",
    "In a wide skillet over very low heat: 1/3 cup of the starchy cooking water, then whisk in the cold butter cubes gradually, about 3 minutes, until emulsified.",
    "Just before the pasta is done, add the lemon juice and zest to the emulsion (late — to keep the lemon flavor fresh).",
    "Drain the pasta 30 seconds before the package time and transfer to the skillet. Cook about a minute until the liquid is absorbed.",
    "Add the cheese gradually, stirring, until the pasta is glossy and creamy — no cream needed. If it dries out, add a splash of cooking water.",
    "Adjust the salt, finish with a drizzle of lemon oil and mint, and serve."
  ],
  tips:"From the comments: no pecorino? Pasta water + a little cream works. Add capers and grilled chicken and it becomes a piccata."
},
{
  id:"10137", diet:"Vegetarian", image:"10137.jpg", category:"Pasta",
  name:"Spaghetti al Limone (Tom Franz)",
  searchAlias:"ספגטי אל לימונה (תום פרנץ)",
  creator:"תום פרנץ - מאסטר שף", time:"10 min", serves:"Serves 2-3",
  video:"https://www.facebook.com/reel/1026004606594050",
  intro:"Browned butter, garlic, and fresh lemon — Amalfi Coast flavors in 10 minutes of work.",
  needs:["pasta","garlic","butter","lemon","basil","parmesan"],
  ingredientLines:[
    {text:"250 g good-quality spaghetti"},
    {text:"3 tbsp olive oil"},
    {text:"40 g butter"},
    {text:"2-3 garlic cloves, thinly sliced"},
    {text:"Grated zest of half a lemon (the yellow part only)"},
    {text:"Juice of half a lemon"},
    {text:"Handful of fresh basil or sage"},
    {text:"Salt + pasta cooking water"},
    {text:"Freshly grated Parmesan to serve"}
  ],
  steps:[
    "Cook the spaghetti to al dente. Reserve a cup of the cooking water and drain.",
    "In a wide skillet, gently brown the garlic in olive oil over medium heat.",
    "Add the butter and cook to a deep golden color with a nutty aroma. Add the lemon zest, lemon juice, and herbs for 20 seconds.",
    "Add half a ladle of cooking water and stir quickly into a smooth sauce.",
    "Add the pasta and toss for about a minute over low heat until the sauce coats it. Add cooking water as needed.",
    "Taste, adjust the salt, and serve with plenty of Parmesan. Like it spicy? Chili flakes or chili oil."
  ],
  tips:"From the comments: adding thinly sliced fennel = a summery delight."
},
{
  id:"10298", diet:"Meat", image:"10298.jpg", category:"Chicken",
  name:"Chicken Stew with Onions & Potatoes",
  searchAlias:"תבשיל עוף עם בצלים ותפוחי אדמה",
  creator:"Hila Adoni", time:"1.5 hrs", serves:"Serves 4",
  video:"https://www.facebook.com/reel/3761940593947494",
  needs:["chicken","onion","potato","garlic","cream-cheese"],
  ingredientLines:[
    {text:"4 pieces of your favorite chicken cuts"},
    {text:"2 white onions"},
    {text:"3 potatoes"},
    {text:"2 garlic cloves, sliced"},
    {text:"1 tsp BBQ spice mix + 1 tsp chicken grill seasoning"},
    {text:"1 tsp cream cheese (Philadelphia)"},
    {text:"1/2 tsp granulated garlic, 1/2 tsp black pepper, 1/2 tsp ground coriander, 1/2 tsp turmeric"},
    {text:"1 tsp salt + olive oil for frying"}
  ],
  steps:[
    "In a wide, hot sauté pan with olive oil, fry the sliced onions until browned. Add the sliced garlic, fry a few more minutes, add the spices, and bloom them well in the oil.",
    "Add the chicken pieces skin-side down, season with pepper and a little salt, cover the pot, and sear until browned. Flip and sear the other side, then add the potato slices.",
    "Pour in boiling water just up to the level of the chicken, cover, and cook over high heat for 10 minutes. Lower the heat and cook about an hour until the chicken is done, then cook 10 more minutes uncovered to reduce."
  ]
},
{
  id:"10460", diet:"Meat", image:"10460.jpg", category:"Beef",
  name:"Oven Brisket — the 'Set It & Go to the Beach' Method",
  searchAlias:"בריסקט בתנור — שיטת 'שימו ולכו לים'",
  creator:"Chen koren", time:"6 hrs (10 min work)",
  video:"https://www.facebook.com/reel/1331260028983256",
  needs:["beef","onion","potato","mustard","honey-silan","parsley"],
  ingredientLines:[
    {text:"1 brisket"},
    {text:"Whole onions"},
    {text:"Small whole potatoes"},
    {text:"Mustard"},
    {text:"Honey"},
    {text:"Salt and pepper"},
    {text:"1 bunch parsley"}
  ],
  steps:[
    "Mix everything together in a roasting pan — the brisket, onions, potatoes, mustard, honey, salt, pepper, and parsley.",
    "Wrap it well in parchment paper and then in foil, nice and tight.",
    "Bake 6 hours in a conventional (static) oven at 160°C (320°F). Set it — and go to the beach 🏖️."
  ]
},
{
  id:"8221", diet:"Vegetarian", image:"8221.jpg", category:"Soups & Sauces",
  name:"5-Minute Miso Soup",
  searchAlias:"מרק מיסו ב-5 דקות",
  creator:"Itai Dagan", time:"10 min", serves:"2 bowls",
  video:"https://www.facebook.com/reel/846772164754668",
  intro:"A bowl full of umami in a few minutes. A great protein hit — 200-300 g of tofu.",
  needs:["dashi","soy","tofu","wakame","miso","scallion"],
  ingredientLines:[
    {text:"1 packet dashi powder"},
    {text:"500-700 ml water"},
    {text:"2 tbsp soy sauce"},
    {text:"250-300 g tofu in small cubes"},
    {text:"Dried wakame (just a little — it swells!)"},
    {text:"1 heaping tsp white miso paste"},
    {text:"Scallions to serve (optional)"},
    {text:"Mushrooms (optional)"}
  ],
  steps:[
    "Put the water, dashi, and soy in a pot. Add the tofu cubes (small cubes — perfect in every spoonful).",
    "Add a little dried wakame. Want mushrooms? Now's the time. Bring to a boil and cook until the tofu softens.",
    "Take off the heat. Dissolve the miso in a small bowl with 2 tbsp of the hot soup until smooth — this prevents lumps.",
    "Return the dissolved miso to the pot, stir, and serve hot with scallions."
  ],
  tips:"Viral comment from Ben Matsumura: never boil the miso (it burns off the flavor) and you don't need the soy — miso is salty enough. Vegan dashi version: grind dried wakame + shiitake in a blender."
},
{
  id:"8367", diet:"Meat", image:"8367.jpg", category:"Chicken",
  name:"Poached Chicken with Ginger-Scallion Sauce",
  searchAlias:"עוף מבושל ברוטב ג'ינג'ר ובצל ירוק",
  creator:"Herman at Home", time:"20 min", serves:"Serves 2",
  video:"https://www.facebook.com/reel/944667481546428",
  intro:"Delicate Chinese-style chicken in an aromatic ginger-scallion sauce. Ready in 20 minutes.",
  needs:["chicken","ginger","scallion","soy","hoisin","wine-white"],
  ingredientLines:[
    {group:"Chicken:"},
    {text:"6 chicken drumsticks"},
    {text:"4 slices ginger"},
    {text:"3 scallions, cut into 5 cm pieces"},
    {text:"1 tbsp Shaoxing wine (optional — or mirin)"},
    {text:"2 tsp salt"},
    {group:"Ginger sauce:"},
    {text:"3 tbsp neutral oil"},
    {text:"3 scallions (white parts) + 1 tbsp chopped green parts"},
    {text:"4 slices ginger"},
    {text:"2 tbsp soy sauce + 1.5 tbsp oyster sauce"},
    {text:"1 tbsp water + 1 tsp sugar + pinch of salt"},
    {text:"To serve: white rice and sliced cucumbers"}
  ],
  steps:[
    "Put the drumsticks in a pot with just enough cold water to cover + ginger, scallions, wine, and salt. Bring to a boil, lower the heat, and simmer 8-10 minutes until the chicken is just done.",
    "Transfer straight to an ice bath to stop the cooking. Once cooled — shred the chicken by hand onto a plate.",
    "For the sauce: fry the scallion whites and ginger in the oil for 5-7 minutes until browned. Strain, keeping the hot oil. Pour it over the chopped scallion greens in a heatproof bowl — it should sizzle. Stir in the soy, oyster sauce, water, sugar, and salt.",
    "Gently reheat the chicken if it has cooled, pour the sauce over, and toss gently. Serve with rice and cucumbers."
  ]
},
{
  id:"8513", diet:"Meat", image:"8513.jpg", category:"Chicken",
  name:"Coconut Lime Chicken (Herman at Home)",
  searchAlias:"עוף בקוקוס וליים (Herman at Home)",
  creator:"Herman at Home", time:"40 min", serves:"Serves 4",
  video:"https://www.facebook.com/reel/1694452798212334",
  intro:"Chicken drumsticks in a citrusy coconut sauce with mushrooms and chili — cheap, simple, and addictive.",
  needs:["chicken","garlic","ginger","chili","scallion","onion","mushrooms","coconut-milk","stock","fish-sauce","lime"],
  ingredientLines:[
    {text:"1 kg chicken drumsticks"},
    {text:"1/2 tsp salt + black pepper + 2 tbsp olive oil"},
    {group:"Sauce:"},
    {text:"4 garlic cloves, crushed"},
    {text:"1 tbsp chopped ginger"},
    {text:"1-2 red chilies (or 1/4 tsp flakes)"},
    {text:"1 scallion, chopped + 1/2 white onion, chopped"},
    {text:"110 g mushrooms, thinly sliced"},
    {text:"1 can (400 ml) full-fat coconut milk"},
    {text:"1 cup chicken stock"},
    {text:"3 tbsp fish sauce + 1 tbsp sugar"},
    {text:"Zest and juice of 2 limes"},
    {text:"For garnish: scallions and chili oil. To serve: rice"}
  ],
  steps:[
    "Pat the chicken dry and season with salt and pepper.",
    "Sear the drumsticks in olive oil, 2-3 minutes per side, until golden (not cooked through), and remove to a plate.",
    "In the same pan: garlic and ginger for 30 seconds, then chili and scallion for another 30 seconds.",
    "Add the onion and mushrooms for 1-2 minutes. Pour in the coconut milk and stock, and stir in the fish sauce, sugar, lime zest and juice, and salt. Bring to a slow, gentle simmer.",
    "Return the chicken to the sauce, cover, and cook over low heat for 15-20 minutes (flipping halfway) until the chicken is tender and done.",
    "Taste and adjust. Serve over rice with scallions and chili oil."
  ]
},
{
  id:"8659", diet:"Vegetarian", image:"8659.jpg", category:"Vegetables & Sides",
  name:"Summer Tomato Tian (Milk Street)",
  searchAlias:"טיאן עגבניות קיץ (Milk Street)",
  creator:"Christopher Kimball's Milk Street", time:"1 hr+",
  video:"https://www.facebook.com/reel/918977704552393",
  intro:"A Provençal casserole that turns even mediocre supermarket tomatoes concentrated and delicious: salting to drain the liquid, then roasting to concentrate the flavor.",
  needs:["tomatoes-fresh","garlic","basil"],
  ingredientLines:[
    {text:"1 kg ripe plum tomatoes, sliced into 1 cm rounds"},
    {text:"6 tbsp olive oil, divided"},
    {text:"4 medium garlic cloves, crushed"},
    {text:"6 sprigs basil"},
    {text:"Coarse salt and black pepper"}
  ],
  steps:[
    "Heat the oven to 220°C (425°F) with a rack in the middle.",
    "Oil a pie dish (23 cm) with 2 tbsp of the oil and scatter half the garlic over the bottom.",
    "Arrange the tomato slices in tight, overlapping circles — they shrink a lot in the oven.",
    "Salt generously (the salting drains off the flavorless liquid), add pepper, scatter the remaining garlic, tuck in the basil sprigs, and drizzle with the remaining oil (4 tbsp).",
    "Bake until the tomatoes are bubbling, browned at the edges, and shrunken (about an hour and a half total).",
    "Cool slightly and serve warm on crusty country bread with cheese. Keeps in the fridge up to a week."
  ],
  tips:"Shortcut from the comments (78 likes): just roast halved Roma tomatoes at 200°C (400°F) with olive oil, salt, and pepper for ~20+ minutes."
},
{
  id:"8815", diet:"Fish", image:"8815.jpg", category:"Pasta",
  name:"Tuna Bolognese (Bolognese Without Meat!)",
  searchAlias:"בולונז טונה (בולונז בלי בשר!)",
  creator:"תום פרנץ - מאסטר שף", time:"60-75 min", serves:"Serves 5-6",
  video:"https://www.facebook.com/reel/1587658772708205",
  intro:"The secret: fry the onion and garlic in the oil from the tuna cans — all those deep flavors go straight into the sauce. Tom has been making this for 25 years.",
  needs:["pasta","tuna","onion","garlic","canned-tomatoes","tomato-paste"],
  ingredientLines:[
    {text:"500 g dried pasta of your choice"},
    {text:"2-4 cans tuna in oil (the oil for frying, the tuna flaked in)"},
    {text:"1 onion, chopped"},
    {text:"2 garlic cloves, thinly sliced"},
    {text:"2 cans crushed tomatoes (400 g each)"},
    {text:"1 small can tomato paste (100 g)"},
    {text:"1 tsp sugar"},
    {text:"1/4 tsp smoked paprika, 1/4 tsp oregano, 1/4 tsp dried basil"},
    {text:"Pinch of crushed chili, salt, and pepper"},
    {text:"1 cup of the pasta cooking water (as needed)"}
  ],
  steps:[
    "In a wide pot, pour in the oil from the tuna cans. Add the onion and cook over medium-low heat for about 15 minutes until soft and caramelized. Toward the end, add the sugar.",
    "Add the garlic and all the spices + the tomato paste. Fry about a minute until it smells rich.",
    "Add the crushed tomatoes and the tuna, flaking it well into the sauce.",
    "Simmer over low heat for 30 minutes to an hour, until the sauce reduces and thickens. Taste and balance the salt/sugar/heat.",
    "If the sauce is too thick — loosen with pasta water. Toss with hot pasta and serve immediately, with mozzarella or Parmesan if you like."
  ]
},
{
  id:"8963", diet:"Meat", image:"8963.jpg", category:"Chicken",
  name:"Korean Ginseng Chicken Soup (Samgyetang)",
  searchAlias:"מרק עוף קוריאני עם ג'ינסנג (סמגיה-טאנג)",
  creator:"Alon Sharaby", time:"4 hrs (15 min work)",
  video:"https://www.facebook.com/reel/1677310753389048",
  intro:"A Korean summer ritual: not a drop of water — all the broth comes from the chicken and cabbage, concentrated and rich.",
  needs:["chicken","ginseng","jujube","cabbage-napa","onion","garlic","ginger","coriander"],
  ingredientLines:[
    {text:"1 whole chicken or leg quarters"},
    {text:"1 ginseng root"},
    {text:"4 jujubes (Chinese dates)"},
    {text:"1/4 napa cabbage in large cubes"},
    {text:"2 white onions, roughly sliced"},
    {text:"1 tsp salt"},
    {text:"6 garlic cloves, peeled and smashed"},
    {text:"1 medium piece of ginger, sliced"},
    {text:"Cilantro leaves for garnish"}
  ],
  steps:[
    "In a large, wide pot (ideally oven-safe): line the bottom with the vegetables in layers.",
    "Arrange the aromatics on top, and the chicken above them.",
    "Add no liquid at all! The cabbage and chicken release all the broth — concentrated and rich.",
    "Cover and cook in the oven or over low heat at 180°C (350°F) for 4 hours.",
    "Arrange the chicken in a bowl, pour the broth over it, and finish with cilantro."
  ]
},
{
  id:"9116", diet:"Vegetarian", image:"9116.jpg", category:"Pasta",
  name:"Mom's Summer Pasta",
  searchAlias:"פסטת הקיץ של אמא (Mom's Summer Pasta)",
  creator:"Maxi's Kitchen", time:"30 min", serves:"Serves 4",
  video:"https://www.facebook.com/reel/2389296691597487",
  intro:"Inspired by The Silver Palate cookbook: a fresh tomato-basil sauce that never touches the stove — the hot pasta does all the work.",
  needs:["pasta","pine-nuts","tomatoes-fresh","basil","parmesan","garlic"],
  ingredientLines:[
    {text:"1/2 cup pine nuts"},
    {text:"450 g ripe tomatoes (about 3 medium), in small cubes"},
    {text:"2 cups fresh basil leaves, in thin ribbons"},
    {text:"170 g Parmigiano-Reggiano in small cubes"},
    {text:"4 garlic cloves, crushed"},
    {text:"1/2 cup extra-virgin olive oil"},
    {text:"1/2 tsp coarse salt + 1/2 tsp cracked black pepper"},
    {text:"450 g linguine"},
    {text:"Flaky Atlantic sea salt to serve"}
  ],
  steps:[
    "Bring a generously salted pot of water to a boil.",
    "Toast the pine nuts in a small skillet over medium heat for 3-5 minutes, stirring constantly, until golden, and transfer immediately to a large bowl (they burn easily).",
    "Add the tomatoes, basil, Parmesan, garlic, olive oil, salt, and pepper to the bowl and mix.",
    "Cook the linguine al dente, drain, and transfer immediately to the bowl with the sauce. Toss with tongs until evenly distributed — the heat lightly melts the cheese.",
    "Plate, sprinkle with flaky salt, and enjoy."
  ],
  tips:"From the comments: a drop of balsamic vinegar is an upgrade; mozzarella works instead of Parmesan; try sweet cherry tomatoes + grated cheese; lemon juice adds freshness. Worried about raw garlic? Give it a quick toss in oil."
},
{
  id:"9271", diet:"Vegetarian", image:"9271.jpg", category:"Vegetables & Sides",
  name:"Naturally Fermented Homemade Pickles 🥒",
  searchAlias:"חמוצים ביתיים בכבישה טבעית 🥒",
  creator:"פרי דן", time:"20 min + 3-7 days",
  video:"https://www.facebook.com/reel/1017927461044811",
  intro:"Natural fermentation in salt brine — no vinegar. Bubbles and cloudy liquid = healthy fermentation, not mold!",
  needs:["cucumbers","lemon","garlic","dill"],
  ingredientLines:[
    {text:"1 kg small cucumbers"},
    {text:"1 lemon, thinly sliced"},
    {text:"1 liter water"},
    {text:"2 tbsp salt"},
    {text:"4-6 garlic cloves"},
    {text:"Fresh dill (optional)"}
  ],
  steps:[
    "Wash the cucumbers and lemon well.",
    "Arrange the cucumbers, lemon slices, garlic, and dill in a jar.",
    "Dissolve the salt in the water and pour it in until all the vegetables are completely covered.",
    "Place a small weight on top so the cucumbers stay below the liquid.",
    "Close loosely and leave at room temperature for 3-7 days (release the gases once a day), until they taste the way you like.",
    "Move to the fridge — fermentation slows down and the pickles keep for weeks."
  ],
  tips:"From the comments: a hot pepper in the jar + dill on top = wow; bay leaves and allspice are nice additions; a grape leaf keeps them crunchy. Seasonal baladi cucumbers are best — regular greenhouse cucumbers turn soft and spongy."
},
{
  id:"9426", diet:"Fish", image:"9426.jpg", category:"Pasta",
  name:"Gabe's Anchovy Pasta (Back-Pocket Pasta)",
  searchAlias:"פסטת האנשובי של גאבה (Back-Pocket Pasta)",
  creator:"Food Network · Gabriele Bertaccini", time:"15 min",
  video:"https://www.facebook.com/reel/1327921729422686",
  intro:"'No recipe needed' — four ingredients you always have at home, aglio e olio style with anchovy depth.",
  needs:["pasta","anchovy","garlic","chili"],
  ingredientLines:[
    {text:"Spaghetti or linguine"},
    {text:"A generous amount of olive oil"},
    {text:"Sliced garlic cloves"},
    {text:"Anchovy fillets (they melt into the sauce)"},
    {text:"Crushed chili flakes"},
    {text:"Pasta cooking water"}
  ],
  steps:[
    "Gently fry the sliced garlic in plenty of olive oil until golden.",
    "Add the anchovies and let them melt into the oil, along with the chili flakes.",
    "Cook the pasta al dente and transfer it to the sauce with a little of the cooking water.",
    "Toss until the sauce coats the pasta and serve."
  ],
  tips:"From the comments: lemon zest and juice at the end are an upgrade; to make it a puttanesca — crushed tomatoes, Kalamata olives, capers, and parsley."
},
{
  id:"9589", diet:"Meat", image:"9589.jpg", category:"Chicken",
  name:"Chicken Thighs with Fennel in Orange Sauce 🍊",
  searchAlias:"פרגיות עם שומר ברוטב תפוזים 🍊",
  creator:"פלפלת", time:"1 hr", serves:"Serves 4",
  video:"https://www.facebook.com/reel/1035851398847288",
  intro:"One pan in the oven: the oranges caramelize and the fennel turns soft and sweet. A scent that fills the whole house.",
  needs:["chicken","orange","fennel","garlic","honey-silan"],
  ingredientLines:[
    {text:"800 g boneless chicken thighs, halved"},
    {text:"1 large orange, cut into slices"},
    {text:"2 fennel bulbs, cut into slices"},
    {group:"Sauce:"},
    {text:"Juice of 2 oranges"},
    {text:"3 garlic cloves, crushed"},
    {text:"1/4 cup honey"},
    {text:"Salt and black pepper to taste"},
    {group:"Glaze:"},
    {text:"2 tbsp date syrup + a little salt and pepper"}
  ],
  steps:[
    "Heat the oven to 200°C (400°F).",
    "Arrange the orange and fennel slices in a baking dish and lay the chicken thighs on top.",
    "Mix the orange juice, garlic, honey, salt, and pepper and pour over the whole dish.",
    "Mix the date syrup with a little salt and pepper and brush over the top of the chicken.",
    "Bake 40-50 minutes until the chicken is browned and the sauce is reduced and caramelized. Finish with 15 minutes under the broiler for nice browning."
  ],
  tips:"From the comments: works with drumsticks/leg quarters too. Chicken breast can dry out — if you use it, shorten the baking time."
},
{
  id:"9456", diet:"Vegetarian", image:"9456.jpg", category:"Vegetables & Sides",
  name:"Chinese-Style Garlic Stir-Fried Broccoli 🥦",
  searchAlias:"ברוקולי מוקפץ עם שום בסגנון סיני 🥦",
  creator:"שחר ואורן", time:"5 min",
  video:"https://www.facebook.com/reel/27980752161529545",
  intro:"You don't like broccoli because you've been making it wrong! Healthy, vegan, gluten-free — and the first thing to disappear from the table.",
  needs:["broccoli","garlic","cornflour"],
  ingredientLines:[
    {text:"400 g broccoli in small florets"},
    {text:"2 tsp oil"},
    {text:"2 garlic cloves, chopped"},
    {text:"1/4 cup water for steaming"},
    {text:"1/2 tsp salt + 1 tsp sugar"},
    {text:"1/2 tbsp cornstarch mixed with 2 tbsp water"}
  ],
  steps:[
    "Heat a wok with the oil and add the garlic right away, while the oil is still cold — you're not browning it, just drawing out the flavor.",
    "When the garlic bubbles gently, add the broccoli and toss so the oil coats it.",
    "Add 1/4 cup water and cover for 1.5-2 minutes until the broccoli is bright green — don't overcook, you want crunch.",
    "Uncover, season with the salt and sugar, and toss.",
    "Add the dissolved cornstarch and stir-fry 30 seconds until the sauce thickens and coats. Serve immediately."
  ]
},
{
  id:"9621", diet:"Vegetarian", image:"9621.jpg", category:"Pasta",
  name:"Caramelized Onion & Chili Crisp Spaghetti",
  searchAlias:"ספגטי בצל מקורמל וצ'ילי קריספ",
  creator:"Cooking with Ruqsida", time:"40 min", serves:"Serves 3-4",
  video:"https://www.facebook.com/reel/4225076117741830",
  intro:"Sweet-spicy-creamy: slowly caramelized onion meets chili crisp, soy, and honey in a cream sauce.",
  needs:["pasta","onion","butter","garlic","chili-crisp","soy","honey-silan","cream","parmesan","parsley"],
  ingredientLines:[
    {text:"225 g thin spaghetti"},
    {text:"1 large white onion, thinly sliced"},
    {text:"1 tbsp olive oil + 4 tbsp butter (divided)"},
    {text:"4 garlic cloves, crushed"},
    {text:"1-2 tbsp chili crisp (to taste) + more to serve"},
    {text:"2 tbsp soy sauce + 2 tbsp honey"},
    {text:"2/3 cup cream (or coconut milk for a dairy-free version)"},
    {text:"1 tsp paprika, 1/2 tsp garlic powder, 1/2 tsp Italian seasoning, 1/2 tsp black pepper"},
    {text:"1/2 cup freshly grated Parmesan"},
    {text:"Parsley for garnish"}
  ],
  steps:[
    "In a large skillet over medium-low heat: olive oil + 2 tbsp butter. Add the onion and cook, stirring often, about 20 minutes until soft and lightly caramelized.",
    "Meanwhile, cook the spaghetti al dente in salted water. Reserve 1/2 cup of the cooking water and drain.",
    "Add the remaining butter and the garlic to the onions for one minute.",
    "Stir in the chili crisp, soy, and honey.",
    "Lower the heat and pour in the cream. Add the spices and cook 5 minutes until slightly thickened.",
    "Stir in the Parmesan until melted and smooth.",
    "Add the pasta and toss until fully coated — loosen with pasta water as needed.",
    "Serve with chili oil and parsley."
  ],
  tips:"From the comments: low heat + a little pasta water keep the cream from breaking; recommended upgrades — shrimp, mushrooms, or chicken."
},
{
  id:"9779", diet:"Vegetarian", image:"9779.jpg", category:"Pasta",
  name:"Spaghetti al Limone (Chef Gianluca)",
  searchAlias:"ספגטי אל לימונה (השף גיאנלוקה)",
  creator:"Gianluca Ruggieri Private Chef", time:"20 min", serves:"1 serving (scale up)",
  video:"https://www.facebook.com/reel/2223339705153783",
  intro:"From the Amalfi Coast — easy to make, hard to master. The trick: a cold-butter emulsion at the end.",
  needs:["pasta","lemon","basil","butter","parmesan"],
  ingredientLines:[
    {text:"85 g spaghetti (per serving)"},
    {text:"1 whole lemon — zest + juice"},
    {text:"7-8 basil leaves"},
    {text:"5 tbsp cold butter, divided"},
    {text:"1 tbsp olive oil"},
    {text:"1/3 cup Parmigiano-Reggiano + more to taste"},
    {text:"Salt, pepper, pasta cooking water"}
  ],
  steps:[
    "Cook the spaghetti in boiling salted water.",
    "While it cooks: in a skillet, combine the olive oil, half the butter, and a ladle of the cooking water.",
    "Add the lemon zest, the juice of half the lemon, and the basil leaves. Cook until slightly thickened.",
    "When the pasta is al dente, transfer it to a bowl with a little cooking water.",
    "Add the sauce from the skillet and toss.",
    "Add the remaining cold butter and stir vigorously to build an emulsion.",
    "Add more lemon zest, basil, and the Parmigiano.",
    "Stir until creamy, adding cooking water as needed. Salt and pepper, and serve immediately."
  ],
  tips:"From the comments: mint instead of basil is wonderful with lemon; you can halve the butter and add more cheese."
},
{
  id:"9937", diet:"Fish", image:"9937.jpg", category:"Fish",
  name:"Steamed Fish on Greens with Asian Sauce 🐠",
  searchAlias:"דג מאודה על מצע ירוקים עם רוטב אסייתי 🐠",
  creator:"Ofir Shar - Personal chef", time:"25 min",
  video:"https://www.facebook.com/reel/28462868789971918",
  intro:"Exactly 9 minutes of steaming — the fish stays tender and the greens stay crisp. The sauce is sweet-sour-spicy.",
  needs:["fish-white","bok-choy","broccoli","snow-peas","lemongrass","vinegar","lemon","fish-sauce","chili","garlic","coriander"],
  ingredientLines:[
    {text:"1 fresh white fish fillet (sea bass, bream, or grouper)"},
    {text:"Bok choy, broccoli florets, snow peas"},
    {text:"1 lemongrass stalk, lightly bruised"},
    {group:"Sauce:"},
    {text:"3 tbsp brown sugar"},
    {text:"3 tbsp water + 3 tbsp vinegar"},
    {text:"2-3 tbsp fresh lemon juice"},
    {text:"3 tbsp fish sauce"},
    {text:"1/2 red chili, finely chopped + 1 garlic clove, chopped"},
    {text:"Small bunch of cilantro, finely chopped"}
  ],
  steps:[
    "In a steamer (bamboo if you have one), arrange the greens on the bottom, and lay the fish and lemongrass on top.",
    "Steam over a pot of boiling water for exactly 9 minutes — the fish is done and the greens stay crisp.",
    "For the sauce: lightly reduce the brown sugar, water, and vinegar until the sugar dissolves. Cool.",
    "Add the lemon juice, fish sauce, chili, garlic, and cilantro and stir.",
    "Drizzle the sauce generously over the fish and greens and serve."
  ]
},
{
  id:"10086", diet:"Meat", image:"10086.jpg", category:"Chicken",
  name:"Spicy Brazilian Coconut Chicken",
  searchAlias:"עוף ברזילאי חריף בקוקוס",
  creator:"Zachs.foods", time:"45 min", serves:"Serves 2-3",
  video:"https://www.facebook.com/reel/1054553393753368",
  intro:"Spice-coated thighs in a tomato-coconut sauce with gochujang depth.",
  needs:["chicken","onion","chili","garlic","ginger","gochujang","canned-tomatoes","lemon","coconut-milk"],
  ingredientLines:[
    {group:"Chicken:"},
    {text:"2 skin-on, bone-in chicken leg quarters"},
    {text:"3 tbsp olive oil"},
    {text:"2 tsp salt + 2 tsp garlic powder"},
    {text:"1 tsp each of smoked paprika, onion powder, ground coriander, and cumin"},
    {group:"Sauce:"},
    {text:"1/2 yellow onion, chopped"},
    {text:"1 jalapeño, chopped"},
    {text:"2 garlic cloves, crushed + 2 tsp chopped ginger"},
    {text:"1 tbsp gochujang"},
    {text:"1.5 cups crushed tomatoes"},
    {text:"Pinch of salt + juice of half a lemon"},
    {text:"1 cup coconut milk"}
  ],
  steps:[
    "Season the chicken with all the spices and sear skin-side down in olive oil until the skin is crisp and browned (over medium heat, patiently — the fat renders). Remove.",
    "In the same pan, sauté the onion and jalapeño until softened, then add the garlic and ginger for a minute.",
    "Add the gochujang, crushed tomatoes, salt, and lemon juice and cook a few minutes.",
    "Pour in the coconut milk and stir into a smooth sauce.",
    "Return the chicken to the sauce and cook over low heat until it's done and the sauce has thickened. Serve with rice."
  ],
  tips:"From the comments: if you're allergic to coconut, swap in cream; you can skip the oil and just slowly render the skin's fat."
},
{
  id:"10237", diet:"Fish", image:"10237.jpg", category:"Fish",
  name:"Salmon Poached in Cream Sauce (The Vivaldi Way)",
  searchAlias:"סלמון מבושל ברוטב שמנת (The Vivaldi Way)",
  creator:"Vivaldi Restaurant", time:"20 min", serves:"1 serving (scale up)",
  video:"https://www.facebook.com/reel/1445758344259595",
  intro:"The 'everything in the pan at once' method — just simmer and reduce. The chef's father's recipe.",
  needs:["salmon","scallion","leek","spinach","stock","wine-white","cream"],
  ingredientLines:[
    {text:"225 g salmon fillet (skinless)"},
    {text:"1/4 cup sliced scallions"},
    {text:"1/4 cup sliced leek"},
    {text:"Handful of baby spinach leaves"},
    {text:"1/2 cup chicken/vegetable/fish stock"},
    {text:"1/4 cup dry white wine"},
    {text:"1 cup heavy cream"},
    {text:"Salt and pepper to taste"}
  ],
  steps:[
    "Put all the ingredients in a skillet at once and cover.",
    "Bring to a gentle simmer and poach the salmon slowly to your preferred doneness.",
    "Remove the salmon and reduce the sauce until thickened.",
    "Pour the sauce over the salmon and serve."
  ],
  tips:"From the comments (hundreds of likes): a spoonful of capers and/or a little dill are a big upgrade."
},
{
  id:"10397", diet:"Fish", image:"10397.jpg", category:"Fish",
  name:"One-Pan Mediterranean Fish",
  searchAlias:"דג ים-תיכוני במחבת אחת",
  creator:"Chef Tom Walton", time:"30 min", serves:"Serves 4",
  video:"https://www.facebook.com/reel/1619723202917852",
  intro:"A tomato-caper-olive ragout that cooks underneath the fish. Serve with crusty country bread, potatoes, or rice.",
  needs:["fish-white","onion","garlic","capers","cherry-tomatoes","olives","capsicum-roasted","parsley","lemon"],
  ingredientLines:[
    {text:"500 g firm white fish fillet (grouper/sea bass/cod)"},
    {text:"Salt, pepper, 3 tbsp olive oil (divided)"},
    {text:"1 onion, finely chopped"},
    {text:"2 garlic cloves, roughly chopped"},
    {text:"4 tbsp capers (divided)"},
    {text:"2 baskets cherry tomatoes"},
    {text:"2 tsp dried oregano"},
    {text:"1/2 cup pitted Kalamata olives (divided)"},
    {text:"1/2 cup roasted pepper strips"},
    {text:"Handful of parsley leaves + lemon wedges to serve"}
  ],
  steps:[
    "Season the fish with salt and pepper, drizzle with half the oil, and gently massage it in. Set aside.",
    "In a large skillet over medium-high heat: the remaining oil, onion, garlic, and a pinch of salt — 3 minutes to soften.",
    "Add half the capers, the cherry tomatoes, and the oregano. Lower the heat and cook until the tomatoes burst — crush them with a fork into a thick ragout, and stir in half the olives.",
    "Nestle the fish into the ragout and scatter the roasted pepper on top.",
    "Cover and cook over low heat for 10-12 minutes until the fish is just cooked.",
    "Serve with the remaining capers and olives, parsley, and lemon."
  ],
  tips:"From the comments: puttanesca-style — the sauce is also great on pasta; a splash of white wine is an upgrade; it's even better the next day."
},
{
  id:"8165", diet:"Fish", image:"8165.jpg", category:"Fish",
  name:"Shabbat Fish Pot (North African Style)",
  searchAlias:"סיר דגים לשבת (בסגנון צפון-אפריקאי)",
  creator:"Chen koren", time:"45 min",
  video:"https://www.facebook.com/reel/661418020298339",
  intro:"A free take on Moroccan fish: peppers and garlic are the base, with tomato and chickpeas. (Reconstructed from the video — Chen sends the full steps by DM.)",
  needs:["fish-white","pepper-red","garlic","tomatoes-fresh","coriander"],
  ingredientLines:[
    {text:"White fish steaks (white grouper/mullet — salmon works too)"},
    {text:"Red peppers, roughly chopped"},
    {text:"Lots of garlic cloves"},
    {text:"1 tomato, chopped"},
    {text:"Cooked chickpeas (optional)"},
    {text:"Olive oil, paprika, salt, pepper"},
    {text:"Cilantro or parsley"}
  ],
  steps:[
    "Line a wide pot with olive oil, the peppers, and the garlic, and fry briefly.",
    "Add the tomato, chickpeas, and spices (paprika generously).",
    "Lay the fish steaks on top and add a little water, up to half the height of the fish.",
    "Cover and cook over low heat until the fish is done and the sauce is thick and red. Finish with cilantro."
  ]
},
{
  id:"8311", diet:"Fish", image:"8311.jpg", category:"Fish",
  name:"Mediterranean Baked Salmon",
  searchAlias:"סלמון ים-תיכוני בתנור",
  creator:"Sofiaa Foodie", time:"25 min", serves:"Serves 3-4",
  video:"https://www.facebook.com/reel/27510381605288898",
  needs:["salmon","red-onion","cherry-tomatoes","capers","olives","thyme","garlic"],
  ingredientLines:[
    {text:"500 g salmon fillet in medium cubes"},
    {text:"1 small red onion, thinly sliced"},
    {text:"200 g cherry tomatoes, halved"},
    {text:"1 tbsp capers"},
    {text:"100 ml olive oil"},
    {text:"100 g pitted olives (green or black)"},
    {text:"Sprigs of fresh thyme"},
    {text:"Crushed garlic + chili flakes (optional)"},
    {text:"Salt, and lemon juice to serve"}
  ],
  steps:[
    "Heat the oven to 180°C (350°F).",
    "In a baking dish: a little olive oil, the red onion, cherry tomatoes, olives, and capers — mix.",
    "Lay the salmon cubes on top and season with salt.",
    "Scatter the thyme (and garlic/chili if using) and drizzle with the remaining olive oil.",
    "Bake 15 minutes until the salmon is just done. Squeeze fresh lemon over and serve with rice or pasta."
  ],
  tips:"From the comments: you can give the vegetables 10 minutes in the oven before adding the salmon; anchovies in the sauce = an upgrade."
},
{
  id:"8455", diet:"Vegetarian", image:"8455.jpg", category:"Pasta",
  name:"Quick Lazy-Day Pasta (David Rocco)",
  searchAlias:"פסטה מהירה לעצלנים (David Rocco)",
  creator:"Vivaldi Restaurant", time:"10 min",
  video:"https://www.facebook.com/reel/837912232740331",
  intro:"'Restaurant-level 10-minute pasta' — tomatoes, fresh chili, and Parmesan. No garlic in the original (but most commenters add it).",
  needs:["pasta","canned-tomatoes","chili","parmesan"],
  ingredientLines:[
    {text:"Spaghetti"},
    {text:"Olive oil"},
    {text:"1 fresh chili, chopped (or a pinch of chili flakes)"},
    {text:"Good-quality canned tomatoes"},
    {text:"Grated Parmesan"},
    {text:"Salt (in the pasta water)"}
  ],
  steps:[
    "Heat the olive oil with the chili in a skillet.",
    "Add the tomatoes and simmer gently for a few minutes, crushing as you go.",
    "Cook the spaghetti in well-salted water and transfer to the sauce with a little cooking water.",
    "Toss, finish with plenty of Parmesan, and serve."
  ],
  tips:"From the comments: a garlic clove adds a lot; if you prefer it milder — halve the chili."
},
{
  id:"8600", diet:"Meat", image:"8600.jpg", category:"Beef",
  name:"Thai Coconut Braised Beef",
  searchAlias:"בקר תאילנדי בקוקוס (Thai Coconut Braised Beef)",
  creator:"Thegoodbite", time:"3 hrs", serves:"Serves 4 (670 calories, 43 g protein)",
  video:"https://www.facebook.com/reel/1004011975510269",
  intro:"Melt-in-your-mouth beef in an aromatic Thai coconut sauce.",
  needs:["beef","coconut-milk","curry-red","garlic","ginger","onion","stock","lime","peanuts"],
  ingredientLines:[
    {text:"800 g slow-cooking beef cut, in large cubes"},
    {text:"Salt and pepper (1 tsp each) + 1 tbsp oil for searing"},
    {text:"2 shallots, finely chopped"},
    {text:"4 garlic cloves, grated + 10 g grated ginger"},
    {text:"2 tbsp Thai red curry paste"},
    {text:"750 ml chicken / beef stock"},
    {text:"2 kaffir lime leaves"},
    {text:"1 can (400 ml) coconut milk"},
    {text:"Juice of 1 lime"},
    {text:"Thai basil leaves + 30 g roasted peanuts, chopped"},
    {text:"To serve: rice, pickled cucumber, and scallions"}
  ],
  steps:[
    "Season the beef cubes with salt and pepper and sear in a heavy pot until browned. Remove.",
    "Sauté the shallots, then the garlic and ginger.",
    "Add the red curry paste and bloom it with a quick fry.",
    "Return the beef, add the stock and lime leaves, cover, and cook over low heat for 2.5 hours until the meat falls apart.",
    "Stir in the coconut milk, and finish with the lime juice and Thai basil.",
    "Serve over rice with the sauce, chopped roasted peanuts, pickled cucumber, and scallions. (Reconstructed from the video + the creator's brother's recipe.)"
  ]
},
{
  id:"8744", diet:"Vegetarian", image:"8744.jpg", category:"Pasta",
  name:"Frozen Lemon Pasta (4 Ingredients)",
  searchAlias:"פסטת לימון קפוא (4 מרכיבים)",
  creator:"Allrecipes · Nicole McLaughlin", time:"15 min (+ freezing the lemon)", serves:"Serves 2-3",
  video:"https://www.facebook.com/reel/2075575389694968",
  intro:"The viral trend: grate a whole frozen lemon — zest, pith, and a bit of the white — straight into the sauce.",
  needs:["pasta","lemon","butter","parmesan"],
  ingredientLines:[
    {text:"1 large unwaxed lemon, completely frozen (overnight in the freezer)"},
    {text:"225 g spaghetti (half a package)"},
    {text:"2 tbsp butter"},
    {text:"3 tbsp grated Parmesan + more to serve"},
    {text:"Black pepper to taste"},
    {text:"1/2 cup reserved cooking water"}
  ],
  steps:[
    "Freeze a washed, dried lemon overnight until completely solid. Cook the spaghetti al dente.",
    "While it cooks: put the butter, Parmesan, and black pepper in a large bowl.",
    "Grate about a third of the frozen lemon — peel, pith, and a bit of the white — straight into the bowl.",
    "Add the pasta with about a quarter cup of cooking water and toss until the butter melts and the cheese forms a glossy sauce. Add more cooking water as needed.",
    "Taste, add Parmesan, and serve."
  ],
  tips:"From the comments: the white part is bitter — some grate only the yellow; anti-bitterness trick: boil the lemon before freezing."
},
{
  id:"8894", diet:"Meat", image:"8894.jpg", category:"Chicken",
  name:"Broiled Lemon Chicken (Rao's Style)",
  searchAlias:"עוף לימון בגריל תנור (בסגנון Rao's)",
  creator:"Sip and Feast", time:"1 hr (+ overnight in the fridge)", serves:"Serves 4",
  video:"https://www.facebook.com/reel/2865372707132171",
  intro:"The Italian-American classic: roast chicken finished under the broiler with a tangy lemon-oregano sauce.",
  needs:["chicken","lemon","garlic","vinegar","butter","parsley","stock"],
  ingredientLines:[
    {text:"1 small whole chicken, split in half (backbone removed)"},
    {text:"4 tsp coarse salt"},
    {text:"3 tbsp olive oil + black pepper"},
    {text:"1 cup chicken stock"},
    {text:"2 tbsp cold butter, cubed"},
    {text:"1/4 cup parsley + lemon slices and zest to serve"},
    {group:"Lemon sauce:"},
    {text:"1/2 cup olive oil"},
    {text:"1/3 cup fresh lemon juice"},
    {text:"1 tbsp red wine vinegar"},
    {text:"5 garlic cloves, crushed"},
    {text:"1 tbsp dried oregano"},
    {text:"1 tsp salt + 1/2 tsp pepper"}
  ],
  steps:[
    "Pat the chicken halves dry, salt them on all sides, and set on a rack in the fridge, uncovered, overnight.",
    "Heat the oven to 260°C (500°F). Take the chicken out an hour before roasting.",
    "Whisk together all the lemon sauce ingredients.",
    "Place the chicken skin-side up in an ovenproof skillet, drizzle with olive oil, add pepper, and pour the stock into the bottom. Roast 25 minutes.",
    "Cut each half into 6 pieces (12 total). Pour off most of the pan juices (leave 1/3 cup).",
    "Return the chicken skin-side up and pour the lemon sauce over it and into the pan.",
    "Move to a low broil for about 10 minutes until the chicken is charred and done (drumsticks may need another 5-10 minutes).",
    "Transfer to a serving platter, whisk the cold butter into the pan sauce with the parsley, and pour over the chicken. Serve with bread."
  ]
},
{
  id:"9051", diet:"Meat", image:"9051.jpg", category:"Chicken",
  name:"Pot Chicken with Grapes — 'Sealed for the Holiday'",
  searchAlias:"עוף עם ענבים בסיר — 'סגורים לחג'",
  creator:"Chen koren", time:"1.5 hrs",
  video:"https://www.facebook.com/reel/951278360535395",
  intro:"In Chen Koren's signature style: no water — the chicken and grapes cook in their own juices. (Reconstructed from the video.)",
  needs:["chicken","grapes","onion"],
  ingredientLines:[
    {text:"Chicken leg quarters / drumsticks"},
    {text:"A bunch of grapes (yes, right in the pot!)"},
    {text:"Onion"},
    {text:"Salt, pepper, and your favorite spices"},
    {text:"A little olive oil"}
  ],
  steps:[
    "Place the onion, chicken, and grapes in a heavy pot.",
    "Season and cover — without adding any water.",
    "Cook over low heat / in the oven until the chicken is tender and the grapes melt into a sweet sauce.",
    "Serve hot with the sauce that forms in the pot."
  ]
},
{
  id:"9358", diet:"Meat", image:"9358.jpg", category:"Beef",
  name:"Shabbat Asado in 10 Minutes of Work",
  searchAlias:"אסאדו לשבת ב-10 דקות עבודה",
  creator:"Liron Azulay", time:"4-5 hrs (10 min work)", serves:"Serves 6",
  video:"https://www.facebook.com/reel/1727591631778405",
  needs:["beef","potato","onion","garlic","tomato-paste","honey-silan","stock"],
  ingredientLines:[
    {text:"1.5-2.5 kg boneless asado (beef short ribs)"},
    {text:"5-6 large potatoes"},
    {text:"2 large onions"},
    {text:"7-10 whole garlic cloves"},
    {group:"Marinade:"},
    {text:"2 tbsp tomato paste (~100 g)"},
    {text:"1 heaping tbsp paprika + 1 level tsp cumin"},
    {text:"Salt and pepper to taste"},
    {text:"2 tbsp pure maple / date syrup / honey"},
    {text:"2 cups water + 1 tbsp chicken bouillon powder (or 2 cups vegetable stock)"}
  ],
  steps:[
    "Halve the onions and quarter the potatoes. Scatter them in a roasting pan, lay the asado on top, and scatter the garlic cloves around.",
    "Mix all the marinade ingredients with half the water and pour over the asado so it covers the vegetables too.",
    "Add the rest of the water — up to about half the height of the asado, no more.",
    "Cover well with parchment paper and then foil, and bake at 160°C (320°F) for 4-5 hours.",
    "Check after 4 hours — keep going until the asado is tender and falling apart."
  ]
},
{
  id:"9679", diet:"Meat", image:"9679.jpg", category:"Chicken",
  name:"Chicken Thighs in a Light Chimichurri",
  searchAlias:"פרגיות בצ'ימיצ'ורי קליל",
  creator:"Chen koren", time:"1.5 hrs (15 min work)",
  video:"https://www.facebook.com/reel/1815847359824482",
  intro:"No water at all — the chicken thighs cook in their own juices inside a green chimichurri. Works with chicken breast too (careful not to dry it out).",
  needs:["chicken","onion","pepper-red","parsley","coriander"],
  ingredientLines:[
    {text:"Boneless chicken thighs"},
    {text:"1 onion, very finely chopped"},
    {text:"1/2 red bell pepper, finely chopped"},
    {text:"Handful of parsley + handful of cilantro, chopped"},
    {text:"A generous pour of olive oil"},
    {text:"Salt, pepper, baharat, and onion powder"}
  ],
  steps:[
    "Chop very finely: the onion, bell pepper, parsley, and cilantro, and mix with olive oil and the spices into a chimichurri.",
    "Marinate the chicken thighs in the chimichurri.",
    "Heat a sauté pan and sear the thighs on both sides — without adding water.",
    "Add the remaining chimichurri, cover, and cook over very low heat for about an hour.",
    "A perfect stew with minimal work."
  ],
  tips:"From the comments: works great with drumsticks and leg quarters too."
},
{
  id:"9207", diet:"Meat", image:"9207.jpg", category:"Beef",
  name:"Mongolian Beef — Just Like the Chinese Restaurant",
  searchAlias:"מנגוליאן ביף — כמו במסעדה סינית",
  creator:"Tali Bar", time:"25 min", serves:"Serves 3-4",
  video:"https://www.facebook.com/reel/1206277021552177",
  intro:"The restaurant trick for tender beef: baking powder and water that the meat absorbs before stir-frying.",
  needs:["beef","soy","sesame-oil","ginger","garlic","teriyaki","hoisin","gochujang","scallion"],
  ingredientLines:[
    {group:"Beef mixture:"},
    {text:"500 g very thin sirloin strips"},
    {text:"1 tbsp baking powder + 1/4 cup water"},
    {text:"1/2 tbsp sugar, 1/2 tsp salt, 1/2 tsp black pepper"},
    {text:"1/4 tsp garlic powder + 1/4 tsp onion powder"},
    {text:"2 tbsp sesame oil"},
    {text:"1/4 cup low-sodium soy sauce"},
    {group:"Mongolian sauce:"},
    {text:"1 tsp grated ginger + 2 garlic cloves, crushed"},
    {text:"1 tbsp brown sugar"},
    {text:"1 tbsp thick teriyaki sauce"},
    {text:"1 tbsp hoisin or mushroom sauce"},
    {text:"1 tsp gochujang (optional, adds a lot)"},
    {text:"1/3 cup soy sauce + 2 tbsp water + a little pepper"},
    {text:"3 scallion stalks, roughly chopped"}
  ],
  steps:[
    "Mix the beef strips with the baking powder and water until the meat absorbs it all — that's the tenderness secret.",
    "Add the rest of the mixture ingredients and mix.",
    "In a bowl, mix all the sauce ingredients except the scallions.",
    "Heat a wok over high heat until it just starts to smoke. Add ~3 tbsp neutral oil and the beef, and fry until seared and browned on all sides.",
    "Add the sauce and cook over high heat for about 5 minutes until reduced.",
    "Add the scallions for the last minute and serve over hot rice."
  ],
  tips:"From the comments: some say baking soda (not baking powder) is the real tenderizer — both work, baking soda is several times stronger (use less)."
},
{
  id:"405", diet:"Meat", image:"405.jpg", category:"Beef",
  name:"Beef & Onion Pot — '2 Minutes of Work'",
  searchAlias:"קדרת בשר ובצל — '2 דקות עבודה'",
  creator:"Chen koren", time:"Overnight on a hot plate / hours in the oven",
  video:"https://www.facebook.com/reel/1509059813562012",
  intro:"No searing, no frying, no stirring: layers of beef and onion in a heavy pot, and time does everything. Kettle-style slow cooking.",
  needs:["beef","onion"],
  ingredientLines:[
    {text:"Stewing beef cuts (neck/shoulder/asado)"},
    {text:"Lots of sliced onion"},
    {text:"Salt and black pepper"},
    {text:"That's it. Really."}
  ],
  steps:[
    "In a heavy pot, arrange a generous layer of onion with the beef pieces on top. Season with salt and pepper.",
    "No water and no oil — the juices of the meat and onion make the sauce.",
    "Cover and cook on a hot plate / very low heat for long hours (Friday to the next day works).",
    "You get melt-in-your-mouth beef in a sweet, rich onion sauce."
  ],
  tips:"From the comments: it works because the closed lid returns the steam to the pot. You can add a bone-in asado piece too."
}
];
