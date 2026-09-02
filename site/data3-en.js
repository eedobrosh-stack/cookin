/* Cookin — batch 3 (2026-08-25): 7 dishes synced from the WhatsApp group */

Object.assign(INGREDIENTS, {
  shrimp:      {label:"Shrimp", group:"Proteins", subs:["chicken"]},
  cauliflower: {label:"Cauliflower", group:"Vegetables & Fruit", subs:["broccoli"]},
  dumplings:   {label:"Frozen dumplings / wontons", group:"Asian Pantry", subs:["noodles"]},
  oregano:     {label:"Oregano", group:"Herbs", subs:["thyme","basil"]},
  rosemary:    {label:"Rosemary", group:"Herbs", subs:["thyme"]}
});

RECIPES.push(
{
  id:"69379", diet:"Fish", image:"69379.jpg", category:"Pasta",
  name:"Garlic Chili Crisp Shrimp Pasta",
  searchAlias:"פסטת שרימפס בשום וצ'ילי קריספ",
  creator:"Chef Fatty", time:"20 min", serves:"Serves 2",
  video:"https://www.facebook.com/reel/1705864810707471",
  intro:"One pan: a sweet-savory butter, garlic, and chili crisp sauce the pasta cooks right in, with shrimp added at the very end. Reconstructed from the video.",
  needs:["pasta","shrimp","butter","garlic","chili-crisp","soy","sugar","scallion"],
  ingredientLines:[
    {text:"200 g spaghetti"},
    {text:"200-250 g peeled and deveined shrimp"},
    {text:"2 tablespoons butter"},
    {text:"4-5 garlic cloves, minced"},
    {text:"1-2 tablespoons chili crisp / chili oil"},
    {text:"2 tablespoons soy sauce"},
    {text:"1 tablespoon brown sugar"},
    {text:"~2 cups water"},
    {text:"Chopped scallions"}
  ],
  steps:[
    "Saute the butter, garlic, and chili crisp in a wide skillet until fragrant.",
    "Add the soy sauce, brown sugar, and water and bring to a boil.",
    "Add the dry pasta straight into the sauce and cook, stirring, until al dente and the sauce is reduced and glossy.",
    "Add the shrimp and cook 2-3 minutes, until pink.",
    "Finish with scallions and serve immediately."
  ],
  tips:"Reconstructed from the video (the full recipe was only sent by DM). Thin with a splash of water if the sauce thickens before the pasta is done."
},
{
  id:"69476", diet:"Meat", image:"69476.jpg", category:"Beef",
  name:"Slow Cooker Sesame-Ginger Beef",
  searchAlias:"בקר שומשום-ג'ינג'ר בסיר איטי",
  creator:"cookwithchel", time:"10 min prep + 8 hours", serves:"Serves 4-6",
  video:"https://www.facebook.com/reel/1314041463913642",
  intro:"Chelsea's: 10 minutes of assembly, slow cooking all day, and the beef falls apart. No cream-of-anything cans. Even her grandma approved.",
  needs:["beef","soy","sugar","stock","sesame-oil","garlic","ginger","vinegar","chili","cornflour","rice","scallion"],
  ingredientLines:[
    {text:"1 kg beef stew cubes"},
    {text:"1/2 cup reduced-sodium soy sauce"},
    {text:"1/3 cup packed brown sugar"},
    {text:"1/4 cup beef stock"},
    {text:"1 tablespoon toasted sesame oil"},
    {text:"4 garlic cloves, crushed"},
    {text:"1.5 tablespoons freshly grated ginger"},
    {text:"1 tablespoon rice vinegar"},
    {text:"1/2 teaspoon chili flakes (or more)"},
    {text:"1 tablespoon cornstarch"},
    {text:"To serve: jasmine rice, scallions, sesame seeds"}
  ],
  steps:[
    "Put the beef in the slow cooker and add everything except the cornstarch: soy sauce, brown sugar, stock, sesame oil, garlic, ginger, vinegar, and chili flakes.",
    "Cover and cook on LOW for 8-9 hours or HIGH for 4-5 hours, until the beef falls apart.",
    "Ladle out about 1/4 cup of the cooking liquid, whisk the cornstarch into it until smooth, and stir it back into the pot.",
    "Cover and cook on HIGH another 20-30 minutes — the sauce gets body and shine.",
    "Serve over jasmine rice with scallions, sesame seeds, and something green. Chili crisp for those who like it."
  ],
  tips:"From the comments (70 likes): sear the beef in a skillet before it goes in the slow cooker — the step everyone skips, and it adds a ton of flavor."
},
{
  id:"69645", diet:"Vegetarian", image:"69645.jpg", category:"Vegetables & Sides",
  name:"Greek Lemon Potatoes (Patates Lemonates)",
  searchAlias:"תפוחי אדמה יווניים בלימון (פטאטס למונאטס)",
  creator:"Maryskouzina", time:"1 hr 15 min", serves:"Serves 4-6",
  video:"https://www.facebook.com/reel/1676036934524575",
  intro:"The soul of Sunday dinner in every Greek home: crispy outside, tender inside, and full of lemon. A tip from grandpa from Constantinople: you can spot a juicy lemon by its smooth, almost soft peel.",
  needs:["potato","lemon","olive-oil","garlic","mustard","stock","oregano"],
  ingredientLines:[
    {text:"1.5 kg potatoes, cut into wedges"},
    {text:"Juice of 2-3 juicy lemons"},
    {text:"1/2 cup extra virgin olive oil"},
    {text:"3-4 garlic cloves, crushed"},
    {text:"1 tablespoon mustard"},
    {text:"1 teaspoon bouillon powder (or a cup of chicken/vegetable stock)"},
    {text:"1 tablespoon dried Greek oregano"},
    {text:"Salt and black pepper"},
    {text:"A little water for the pan"}
  ],
  steps:[
    "Preheat the oven to 200°C.",
    "Make the 'Greek elixir': whisk together the lemon juice, olive oil, garlic, mustard, bouillon powder, oregano, salt, and pepper.",
    "Arrange the potato wedges in a baking pan, pour the sauce over, and add a little water to the bottom.",
    "Bake covered with foil for about 40 minutes, then uncover and continue another 20-25 minutes until golden.",
    "Check midway that there's enough liquid in the pan. Serve with the sauce left in the bottom."
  ],
  tips:"From the comments: every Greek home has its own twist — some skip the mustard and garlic ('black pepper is what makes the lemon bloom'), and some add cubes of butter on top."
},
{
  id:"69646", diet:"Vegetarian", image:"69646.jpg", category:"Vegetables & Sides",
  name:"Whole Roasted Cauliflower, Eyal Shani Style",
  searchAlias:"כרובית שלמה בסגנון אייל שני",
  creator:"רובי מיכאל - Rubi Michael", time:"50 min", serves:"Serves 4",
  video:"https://www.facebook.com/reel/1877893009760824",
  intro:"Just 3 ingredients: cauliflower, olive oil, and sea salt. The secret — a quick boil in water as salty as the sea, then a blazing-hot oven until deeply browned.",
  needs:["cauliflower","olive-oil"],
  ingredientLines:[
    {text:"1 cauliflower, as small and young as possible"},
    {text:"4 tablespoons good olive oil"},
    {text:"1 level tablespoon Atlantic sea salt"}
  ],
  steps:[
    "Preheat the oven to 230°C (convection or top-bottom heat).",
    "Bring a huge pot of water, 3/4 full, to a boil with salt — the water should be as salty as the sea (like pasta water).",
    "When the water boils, lower in the cauliflower upside down, leaves on, for exactly 9 minutes and not a second more (worried about worms? remove the leaves).",
    "Transfer to a tray lined with parchment paper. Don't wipe off the liquid — you need it.",
    "Drizzle with the olive oil, sprinkle with the salt, and put straight into the oven for 35 minutes, or until deeply browned.",
    "Serve hot, wrapped in fresh parchment paper."
  ],
  tips:"From the comments: an upgrade — after the boil, coat the cauliflower in mustard mixed with olive oil, fresh thyme, and salt."
},
{
  id:"69663", diet:"Meat", image:"69663.jpg", category:"Chicken",
  name:"Butter Chicken with Rice (Easy Meals for Two)",
  searchAlias:"באטר צ'יקן עם אורז (ארוחות קלות לזוג)",
  creator:"Foodie.Randy", time:"35 min", serves:"Serves 2-3",
  video:"https://www.facebook.com/reel/1762340964926846",
  intro:"Episode 4 of 'Easy Meals for Two': chicken marinated in yogurt and garam masala in a creamy tomato sauce. The running joke in the comments: there's no butter in it at all — and it still works.",
  needs:["chicken","greek-yogurt","onion","ginger","garlic","canned-tomatoes","tomato-paste","cream","rice","coriander"],
  ingredientLines:[
    {group:"Marinade:"},
    {text:"450 g boneless chicken thighs, cubed"},
    {text:"1/2 cup (120 g) full-fat yogurt"},
    {text:"1 teaspoon garam masala + 1 teaspoon salt + 1 teaspoon pepper"},
    {group:"Sauce:"},
    {text:"2 tablespoons olive oil"},
    {text:"1/2 onion, chopped"},
    {text:"1 teaspoon minced ginger + 3 garlic cloves"},
    {text:"1 teaspoon smoked paprika + 1 teaspoon cumin + 1 teaspoon garam masala"},
    {text:"120 g crushed tomatoes + 1 tablespoon tomato paste"},
    {text:"1/2 cup water + 1/2 cup heavy cream"},
    {text:"To serve: rice, a splash of cream, and chopped cilantro"}
  ],
  steps:[
    "Mix the chicken with the yogurt, garam masala, salt, and pepper (marinate 30 minutes for maximum flavor — or skip it if you're hungry).",
    "Sear the chicken in oil over medium-high heat until browned, 6-8 minutes, without crowding the pan (crowded = watery chicken). It doesn't need to be cooked through.",
    "Pour in 1-2 tablespoons of water and scrape up the browned bits from the bottom of the pan; add the onion, garlic, and ginger for 1-2 minutes.",
    "Add the tomato paste for 1-2 minutes, then the crushed tomatoes and the water.",
    "Add the cream and the remaining spices, simmer gently for a few minutes, and return the chicken.",
    "Cook about 10 minutes. Serve over rice with a drizzle of cream and cilantro."
  ],
  tips:"Want it to live up to its name? Stir a tablespoon of butter into the sauce at the end."
},
{
  id:"70230", diet:"Meat", image:"70230.jpg", category:"Soups & Sauces",
  name:"Wonton Soup in Thai Red Curry",
  searchAlias:"מרק וונטונים בקארי אדום תאילנדי",
  creator:"Deeran's Page", time:"20 min", serves:"Serves 2",
  video:"https://www.facebook.com/reel/1559699102322979",
  intro:"A genius shortcut: frozen dumplings cook on the side, then get topped with a coconut red curry broth that's ready in 10 minutes.",
  needs:["coconut-milk","stock","curry-red","onion","garlic","ginger","dumplings","scallion"],
  ingredientLines:[
    {text:"1 cup coconut milk"},
    {text:"1 cup chicken stock"},
    {text:"2 tablespoons red curry paste"},
    {text:"1/2 white onion, chopped"},
    {text:"5 garlic cloves, minced"},
    {text:"1 tablespoon minced ginger"},
    {text:"Frozen dumplings (wontons / gyoza)"},
    {text:"Scallions for garnish"}
  ],
  steps:[
    "Saute the onion, ginger, and garlic until translucent and fragrant.",
    "Add the curry paste, stir, and fry 2-3 minutes.",
    "Pour in the coconut milk and stock and stir over medium heat until the paste dissolves into the liquid.",
    "Meanwhile, cook the dumplings in boiling water according to the package instructions.",
    "Place the dumplings in a bowl, ladle the broth over, garnish with scallions, and serve."
  ],
  tips:"From the comments: make the dumplings yourself — it's fun, tastier, and you can do it together."
},
{
  id:"70229", diet:"Vegetarian", image:"70229.jpg", category:"Pasta",
  name:"Garlic Confit Butter Pasta (from a Chef in Italy)",
  searchAlias:"פסטת שום קונפי וחמאה (משף באיטליה)",
  creator:"Camila Masullo", time:"50 min", serves:"Serves 4",
  video:"https://www.facebook.com/reel/1987788335198116",
  intro:"A chef's take on aglio e olio: whole garlic slow-roasted in olive oil and rosemary, blended into a butter-Parmesan cream that coats the pasta in a silky sauce.",
  needs:["pasta","garlic","olive-oil","rosemary","butter","parmesan","parsley","lemon"],
  ingredientLines:[
    {text:"400 g pasta"},
    {text:"3 heads of garlic, peeled (the cloves)"},
    {text:"150 ml olive oil (to cover the garlic)"},
    {text:"1 sprig fresh rosemary"},
    {text:"80 g softened butter"},
    {text:"50 g grated Parmesan"},
    {text:"3 tablespoons parsley"},
    {text:"Crushed red chili flakes + lemon zest"},
    {text:"1 cup pasta cooking water"}
  ],
  steps:[
    "Place the garlic cloves in a small baking dish, cover with olive oil, add the rosemary, and roast at 170-180°C until soft and golden (~30-40 min).",
    "In a food processor, blend the roasted garlic (without the oil) with the softened butter, Parmesan, parsley, lemon zest, salt, and pepper until you have a smooth cream.",
    "Cook the pasta to al dente and reserve a cup of the cooking water.",
    "Over low heat, toss the hot pasta with the garlic cream, adding the cooking water a little at a time until the sauce is silky and glossy.",
    "Serve with more Parmesan and chili flakes."
  ],
  tips:"Bonus: the leftover confit oil is infused with garlic and rosemary — great for bread and salads."
}
);

/* batch 4 (2026-08-28): 9 dishes synced from the WhatsApp group */

Object.assign(INGREDIENTS, {
  maple:              {label:"Maple syrup", group:"Pantry & Canned", subs:["honey-silan"]},
  brandy:             {label:"Brandy / cognac", group:"Pantry & Canned", subs:["wine-white"]},
  vodka:              {label:"Vodka", group:"Pantry & Canned", subs:[]},
  pear:               {label:"Pear", group:"Vegetables & Fruit", subs:[]},
  pecorino:           {label:"Pecorino", group:"Dairy", subs:["parmesan"]},
  "wine-red":         {label:"Dry red wine", group:"Pantry & Canned", subs:["wine-white"]},
  "peppercorns-green":{label:"Green peppercorns", group:"Pantry & Canned", subs:["pepper"]},
  "cherry-peppers":   {label:"Pickled hot peppers", group:"Pantry & Canned", subs:["chili"]}
});

RECIPES.push(
{
  id:"70354", diet:"Meat", image:"70354.jpg", category:"Chicken",
  name:"Lemon-Dill Chicken over Whipped Mashed Potatoes",
  searchAlias:"עוף בלימון ושמיר על פירה מוקצף",
  creator:"Platesbyalina", time:"35 min", serves:"Serves 2-3",
  video:"https://www.facebook.com/reel/2254704958647072",
  intro:"A meal you'll make again and again: seared chicken breast in a butter-lemon-dill sauce, over mashed potatoes whipped in a stand mixer until they look like a cloud.",
  needs:["chicken","potato","butter","milk","flour","stock","lemon","dill","spices"],
  ingredientLines:[
    {text:"For the mash: potatoes, butter, and warm milk"},
    {text:"Chicken breasts (seasoned with paprika, black pepper, and salt)"},
    {text:"1 tablespoon butter"},
    {text:"1 tablespoon flour (to thicken)"},
    {text:"Chicken stock or cream"},
    {text:"Fresh lemon juice"},
    {text:"Finely chopped dill and/or chives"}
  ],
  steps:[
    "Season the chicken breasts generously and sear in a blazing-hot skillet with a little butter/oil until golden. Set aside.",
    "In the same skillet, melt a knob of butter, add the flour, and stir into a quick roux.",
    "Pour in the cream/stock, squeeze in fresh lemon juice, and cook until the sauce is smooth.",
    "Return the chicken to the sauce, scatter over plenty of dill, and cook another minute.",
    "Whip the boiled potatoes in a stand mixer with butter and warm milk until cloud-like.",
    "Plate it up: mash, chicken, and plenty of the sauce over the top."
  ],
  tips:"From the comments: a wedge of garlic-and-herb cheese (or a mild grated cheese) and a little mustard in the sauce deepen the flavor."
},
{
  id:"70579", diet:"Vegetarian", image:"70579.jpg", category:"Pasta",
  name:"Steve's Pasta — Garlic, Spinach, and Hot Peppers",
  searchAlias:"הפסטה של סטיב — שום, תרד ופלפלים חריפים",
  creator:"Vivaldi (Chef Steve)", time:"20 min", serves:"Serves 2",
  video:"https://www.facebook.com/reel/1347402237497272",
  intro:"\"Not everything has to be super technical\": the chef of Vivaldi throws everything into a cold pan — garlic, mushrooms, pickled hot peppers, and spinach — proving great pasta doesn't need rules. Reconstructed from the video.",
  needs:["pasta","garlic","olive-oil","mushrooms","cherry-peppers","spinach","wine-white","parmesan","parsley"],
  ingredientLines:[
    {text:"Pasta (about 200 g)"},
    {text:"Lots of sliced garlic"},
    {text:"Good olive oil"},
    {text:"A handful of sliced mushrooms"},
    {text:"Lots of sliced pickled hot cherry peppers"},
    {text:"A big handful of spinach"},
    {text:"Salt and pepper"},
    {text:"A splash of white wine"},
    {text:"Lots of grated cheese + parsley"}
  ],
  steps:[
    "Drop the pasta into boiling water; meanwhile, build the pan — no preheating.",
    "Into the pan: a generous pour of olive oil, lots of garlic, the mushrooms, and the hot peppers.",
    "Add the spinach with salt and pepper — it wilts in seconds, so it doesn't matter whether it goes in first or last.",
    "When everything is almost done, pour in a splash of white wine and let it reduce.",
    "Transfer the pasta in with a little of the cooking water and toss.",
    "Finish with lots of cheese and parsley. It has no name — just call it \"Steve's pasta\"."
  ],
  tips:"From the comments: sun-dried tomatoes and pitted Kalamata olives work great here. The chef loves the vinegar tang and heat of the pickled peppers — don't skip them."
},
{
  id:"70584", diet:"Meat", image:"70584.jpg", category:"Chicken",
  name:"Chicken with Orange, Maple, and Cognac",
  searchAlias:"עוף בתפוזים, מייפל וקוניאק",
  creator:"Vivaldi (Chef Steve)", time:"30 min", serves:"Serves 2",
  video:"https://www.facebook.com/reel/1519722963271780",
  intro:"Not the deep-fried takeout Orange Chicken: a chef's version with a real orange sauce — juice, zest, and segments — plus brandy, maple, and butter kneaded with flour.",
  needs:["chicken","orange","stock","maple","butter","flour","brandy","olive-oil"],
  ingredientLines:[
    {text:"2 chicken breasts, butterflied"},
    {text:"1/2 cup orange juice"},
    {text:"1 tablespoon orange zest"},
    {text:"1/4 cup orange segments"},
    {text:"1/2 cup chicken stock"},
    {text:"2 tablespoons maple syrup"},
    {text:"2 tablespoons butter + 3 tablespoons flour"},
    {text:"1 tablespoon brandy"},
    {text:"1 tablespoon olive oil, salt and pepper"}
  ],
  steps:[
    "Season the chicken with salt and pepper and dust lightly with flour.",
    "Heat a skillet with olive oil and brown the chicken about 3 minutes per side. Remove.",
    "Pour the orange juice, chicken stock, and orange zest into the pan and bring to a boil.",
    "Add the brandy and let the alcohol cook off.",
    "Return the chicken and add the maple syrup.",
    "Add the butter kneaded with flour (beurre manié) and stir.",
    "Reduce the sauce to your desired consistency and add the orange segments.",
    "Taste, adjust the seasoning, and serve."
  ],
  tips:"\"Butter kneaded with flour\" = beurre manié, thickens sauces with no lumps. No brandy? Leave it out or swap in a little white wine."
},
{
  id:"70612", diet:"Meat", image:"70612.jpg", category:"Chicken",
  name:"Rosemary Chicken with Mushrooms and Red Wine",
  searchAlias:"עוף רוזמרין עם פטריות ויין אדום",
  creator:"Vivaldi (Chef Steve)", time:"30 min", serves:"Serves 2-3",
  video:"https://www.facebook.com/reel/1086158347095188",
  intro:"Quick and easy: flour-dusted chicken breast in a mushroom-scallion sauce with fresh rosemary, red wine, and chicken stock that reduces around it.",
  needs:["chicken","butter","rosemary","scallion","mushrooms","wine-red","stock","flour","parsley"],
  ingredientLines:[
    {text:"2-3 chicken breasts, halved and flattened, seasoned with salt and pepper and dusted with flour"},
    {text:"1 tablespoon butter"},
    {text:"1 teaspoon chopped fresh rosemary"},
    {text:"3 scallions, sliced"},
    {text:"2 cups sliced mushrooms (cremini or white)"},
    {text:"1/3 cup dry red wine"},
    {text:"2 cups chicken stock"},
    {text:"3 tablespoons butter kneaded with flour"},
    {text:"2 tablespoons chopped parsley"}
  ],
  steps:[
    "Sear the chicken 2-4 minutes per side and remove from the pan.",
    "Add a tablespoon of butter, the mushrooms, and the scallions, and cook until the mushrooms release their liquid.",
    "Add the rosemary and red wine and reduce by half.",
    "Return the chicken and add the chicken stock.",
    "Bring to a boil and add the butter kneaded with flour.",
    "Reduce the sauce to your desired consistency; if the chicken is done before the sauce, take it out.",
    "Finish with parsley and pour the sauce over the chicken."
  ],
  tips:"Don't drink alcohol? Replace the wine with more stock plus a teaspoon of balsamic vinegar."
},
{
  id:"70614", diet:"Vegetarian", image:"70614.jpg", category:"Pasta",
  name:"Penne alla Vodka",
  searchAlias:"פנה אלה וודקה",
  creator:"Ajaya Lama", time:"25 min", serves:"Serves 2",
  video:"https://www.facebook.com/reel/924284176770471",
  intro:"The Italian-American classic: creamy, spicy, tomatoey, and silky — caramelized tomato paste, vodka, and cream coming together into one pink sauce.",
  needs:["pasta","olive-oil","garlic","onion","chili","tomato-paste","vodka","cream","basil","parmesan"],
  ingredientLines:[
    {text:"150 g penne"},
    {text:"1.5 tablespoons olive oil"},
    {text:"1/2 tablespoon sliced garlic"},
    {text:"1 tablespoon finely chopped onion"},
    {text:"1 teaspoon chili flakes"},
    {text:"2 tablespoons tomato paste"},
    {text:"1/4 cup (60 ml) vodka"},
    {text:"1 cup (300 ml) heavy cream"},
    {text:"Fresh basil + 2-4 tablespoons Parmesan"},
    {text:"Salt, black pepper, and pasta water"}
  ],
  steps:[
    "Heat the olive oil and saute the garlic, onion, and chili flakes until golden and fragrant.",
    "Add the tomato paste and fry about a minute, until caramelized.",
    "Pour in the vodka and reduce (flambe only if you're sure of yourself!).",
    "Add the cream, reduce slightly, and season with salt and pepper.",
    "Add the al dente penne and toss until fully coated.",
    "Finish with basil, Parmesan, and a little pasta water for a silky texture.",
    "Serve — upgrade with stracciatella, burrata, or mozzarella on top."
  ],
  tips:"From the comments: pancetta or bacon fried with the onion adds depth (if you're not keeping it vegetarian)."
},
{
  id:"70708", diet:"Vegetarian", image:"70708.jpg", category:"Pasta",
  name:"Cacio e Pere — Pecorino and Pear Pasta",
  searchAlias:"קאצ'ו אה פרה — פסטת פקורינו ואגסים",
  creator:"Gianluca Ruggieri Private Chef", time:"20 min", serves:"Serves 1-2",
  video:"https://www.facebook.com/reel/1404264194883877",
  intro:"\"Don't tell the farmer how good cheese is with pears\" — an old Italian proverb turned into a pasta: a pecorino-pepper cream with sauteed pear cubes.",
  needs:["pear","pecorino","pasta","pepper","olive-oil"],
  ingredientLines:[
    {text:"1 ripe pear"},
    {text:"4 generous tablespoons grated pecorino"},
    {text:"80 g pasta"},
    {text:"Freshly cracked black pepper, generously"},
    {text:"Olive oil, salt"}
  ],
  steps:[
    "Dice the pear and saute in olive oil with salt and pepper. Set aside.",
    "In a small bowl, mix the pecorino with cracked pepper and about 1/8 cup of pasta water until it forms a paste.",
    "Cook the pasta until almost done.",
    "In the hot skillet, add a ladle of pasta water and more pepper, then the pasta.",
    "Add the pears and the pecorino paste.",
    "Toss over low heat until everything melts and coats the pasta. Serve immediately."
  ],
  tips:"From the comments: walnuts sauteed along with the pears — a winning upgrade."
},
{
  id:"70709", diet:"Vegetarian", image:"70709.jpg", category:"Pasta",
  name:"Paccheri with Roasted Tomatoes and Basil",
  searchAlias:"פקרי בעגבניות צלויות ובזיליקום",
  creator:"Sebastian Fitarau", time:"60 min", serves:"Serves 2",
  video:"https://www.facebook.com/reel/3251537631710073",
  intro:"Pomodoro sauce, oven technique: cherry tomatoes / plum tomato wedges roast for 45 minutes with garlic and basil until caramelized, then get blended into a thick, deeply flavored sauce.",
  needs:["pasta","tomatoes-fresh","garlic","olive-oil","basil","parmesan"],
  ingredientLines:[
    {text:"180 g paccheri (paccheri rigati)"},
    {text:"350 g plum (Roma) tomatoes"},
    {text:"3 garlic cloves"},
    {text:"Extra virgin olive oil"},
    {text:"Fresh basil"},
    {text:"Grated Grana / Parmesan, salt"}
  ],
  steps:[
    "Halve the tomatoes into a baking pan with the garlic, basil, olive oil, and salt.",
    "Roast at 180°C for about 45 minutes, until the tomatoes are caramelized.",
    "Remove the garlic cloves and blend the roasted tomatoes into a smooth sauce.",
    "Cook the paccheri to al dente.",
    "Combine the pasta with the sauce in a skillet with a little pasta water.",
    "Finish with fresh basil, Grana, and olive oil."
  ],
  tips:"From the Italian comments: if the basil burns in the oven, add it only at the end of roasting. Oven-roasting gives the tomatoes a caramelized flavor a stovetop sauce can't match."
},
{
  id:"70740", diet:"Meat", image:"70740.jpg", category:"Beef",
  name:"Beef Tenderloin in Green Peppercorn Sauce (Filetto al Pepe Verde)",
  searchAlias:"פילה בקר ברוטב פלפל ירוק (Filetto al Pepe Verde)",
  creator:"Gianluca Ruggieri Private Chef", time:"25 min", serves:"Serves 1-2",
  video:"https://www.facebook.com/reel/1402944661657388",
  intro:"An Italian restaurant classic: flour-dusted tenderloin seared, flambeed in cognac, and finished in a cream-mustard sauce with green peppercorns.",
  needs:["beef","butter","oil","mustard","cream","peppercorns-green","stock","flour","brandy"],
  ingredientLines:[
    {text:"1 beef tenderloin steak, about 170 g (6 oz)"},
    {text:"2 tablespoons butter + 1 tablespoon oil"},
    {text:"1 tablespoon mustard"},
    {text:"3/4 cup heavy cream"},
    {text:"2 tablespoons green peppercorns"},
    {text:"1/3 cup beef stock"},
    {text:"1/3 cup cognac"},
    {text:"Flour for dusting, salt"}
  ],
  steps:[
    "Lightly dust the tenderloin with flour and shake off the excess.",
    "Heat the butter and oil over medium-high heat.",
    "Sear the tenderloin 2 minutes per side until browned.",
    "Pour in the cognac and carefully flambe. Remove the beef.",
    "Toast the green peppercorns in the pan for about a minute.",
    "Add the mustard, cream, and beef stock and stir.",
    "Return the beef and coat it in the sauce for about 3 minutes, then remove to rest.",
    "Reduce the sauce a little and pour it over the beef."
  ],
  tips:"From the comments: too-low heat beats too-high — a cream sauce at a hard boil breaks. This is a close cousin of the French steak au poivre."
},
{
  id:"70851", diet:"Fish", image:"70851.jpg", category:"Fish",
  name:"Lime-Zest Salmon over Roasted Vegetables",
  searchAlias:"סלמון בגרידת ליים על ירקות צלויים",
  creator:"אבי לוי", time:"50 min", serves:"Serves 4",
  video:"https://www.facebook.com/reel/4600723376870624",
  intro:"By Avi Levy: a whole salmon fillet on a bed of roasted potatoes and peppers, in a marinade of lime, honey, garlic, and paprika — the aroma from the zest is incredible.",
  needs:["salmon","potato","pepper-red","chili","spices","garlic","lime","honey-silan","olive-oil"],
  ingredientLines:[
    {text:"1 whole fresh salmon fillet (best left uncut)"},
    {text:"3 potatoes, peeled and sliced"},
    {text:"2 red bell peppers, cut into quarters"},
    {text:"2 hot peppers, halved"},
    {text:"1 teaspoon sweet paprika, 1 teaspoon coarse salt, 1 teaspoon cracked pepper"},
    {text:"About 5 tablespoons olive oil (for the vegetables)"},
    {text:"Sauce: 3 crushed garlic cloves, zest of 1 lime, 1 tablespoon honey"},
    {text:"2 teaspoons paprika, 1 teaspoon cracked pepper, 2 teaspoons coarse salt"},
    {text:"1/4 cup olive oil + juice of 2 limes"}
  ],
  steps:[
    "Arrange the potatoes and peppers in a baking pan with the seasonings and olive oil.",
    "Roast 20 minutes at 180°C.",
    "Trim the fatty edges off the salmon and lay it on the roasted vegetables.",
    "Mix all the sauce ingredients and brush the fish on all sides.",
    "Bake uncovered at 180-200°C for about 20 minutes.",
    "If you cut the fillet into portions, shorten to 15 minutes."
  ],
  tips:"The magic is the lime zest in the sauce — don't skip it. You can marinate ahead, but brushing it on right before baking works great too."
}
);
