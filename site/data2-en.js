/* Cookin — batch 2 (2026-08-16): 29 dishes synced from the WhatsApp group (incl. April-May backfill) — English */

Object.assign(INGREDIENTS, {
  hummus:       {label:"Hummus (prepared spread)", group:"Pantry & Canned", subs:[]},
  mint:         {label:"Mint", group:"Herbs", subs:["basil"]},
  eggs:         {label:"Eggs", group:"Proteins", subs:[]},
  mozzarella:   {label:"Mozzarella", group:"Dairy", subs:["parmesan"]},
  burrata:      {label:"Burrata", group:"Dairy", subs:["mozzarella"]},
  "greek-yogurt":{label:"Greek yogurt", group:"Dairy", subs:["sour-cream"]},
  "sour-cream": {label:"Sour cream", group:"Dairy", subs:["greek-yogurt","cream"]},
  "peanut-butter":{label:"Peanut butter", group:"Pantry & Canned", subs:[]},
  noodles:      {label:"Noodles / ramen", group:"Pantry & Canned", subs:["pasta"]},
  cashews:      {label:"Cashews", group:"Pantry & Canned", subs:["peanuts"]},
  sprouts:      {label:"Bean sprouts", group:"Vegetables & Fruit", subs:[]},
  worcester:    {label:"Worcestershire sauce", group:"Pantry & Canned", subs:["soy"]},
  carrots:      {label:"Carrots", group:"Vegetables & Fruit", subs:[]},
  semolina:     {label:"Semolina", group:"Pantry & Canned", subs:[]},
  beets:        {label:"Beets", group:"Vegetables & Fruit", subs:[]},
  truffle:      {label:"Truffle / truffle oil", group:"Pantry & Canned", subs:[]},
  sriracha:     {label:"Sriracha / sambal", group:"Asian Pantry", subs:["chili-crisp","chili"]}
});

RECIPES.push(
{
  id:"46324", diet:"Vegetarian", image:"46324.jpg", category:"Pasta",
  name:"Butter & Chili Oil Pasta",
  searchAlias:"פסטה בחמאה ושמן צ'ילי",
  creator:"Chhaya Joshi", time:"25 min", serves:"Serves 2-3",
  video:"https://www.facebook.com/reel/2095923627919742",
  intro:"Chhaya's obsession: a sweet-spicy chili-cream sauce that gets darker and deeper the longer it sits.",
  needs:["pasta","garlic","butter","chili-crisp","cream","lime","parmesan","soy","parsley"],
  ingredientLines:[
    {text:"200 g dried pasta"},
    {text:"1 tbsp olive oil"},
    {text:"6-7 garlic cloves, crushed"},
    {text:"2 tbsp butter"},
    {text:"1-2 tbsp chili oil / chili crisp"},
    {text:"1-1.5 cups heavy cream"},
    {text:"1 tsp salt"},
    {text:"Juice of half a lime"},
    {text:"1/4-1/2 cup Parmesan"},
    {text:"1 tbsp soy sauce"},
    {text:"1 cup pasta water + chopped parsley"}
  ],
  steps:[
    "Cook the pasta one minute short of the package directions — it will finish in the sauce.",
    "Heat the olive oil and fry the garlic for 30 seconds.",
    "Add a tablespoon of chili oil and the butter and stir.",
    "Add the cream, salt, and lime juice.",
    "Add the Parmesan and let the sauce thicken for 1-2 minutes.",
    "Add the pasta, more Parmesan, parsley, soy sauce, and pasta water.",
    "One more spoonful of chili oil, toss everything together, and serve garnished with parsley and Parmesan."
  ],
  tips:"From the comments: coconut cream instead of heavy cream works beautifully with the chili oil; upgrade with shrimp or chicken sausages."
},
{
  id:"45042", diet:"Vegetarian", image:"45042.jpg", category:"Pasta",
  name:"Hummus Pasta (NYT — Recipes of the Year)",
  searchAlias:"פסטת חומוס (NYT — מתכוני השנה)",
  creator:"foodiligence · NYT Cooking", time:"20 min", serves:"Serves 3-4",
  video:"https://www.facebook.com/reel/1494837178664781",
  intro:"From the New York Times' top 50 recipes of 2025: hummus spread turns into a creamy, vegan pasta sauce.",
  needs:["pasta","garlic","onion","hummus","lemon"],
  ingredientLines:[
    {text:"340 g bucatini (or spaghetti)"},
    {text:"1/4 cup olive oil"},
    {text:"4 garlic cloves"},
    {text:"1 large shallot"},
    {text:"1 cup hummus (smooth spread)"},
    {text:"1 lemon — zest and juice"},
    {text:"Salt"}
  ],
  steps:[
    "Cook the pasta in well-salted water until al dente. Reserve a cup of the cooking water and drain.",
    "In a large skillet over medium heat: olive oil, garlic, shallot, and a pinch of salt — about 2 minutes until slightly softened.",
    "Stir in the hummus and half a cup of pasta water until you have a smooth, loose sauce. Add the lemon zest and juice.",
    "Over medium-low heat, add the pasta and toss well. Adjust the salt and loosen with pasta water as needed.",
    "Serve with a drizzle of olive oil, fresh herbs, and sesame seeds."
  ],
  tips:"From the comments: a similar version with tahini instead of hummus, topped with crispy air-fryer chickpeas."
},
{
  id:"46225", diet:"Vegetarian", image:"46225.jpg", category:"Vegetables & Sides",
  name:"Green Spinach Shakshuka with Mozzarella & Chili",
  searchAlias:"שקשוקת תרד ירוקה עם מוצרלה וצ'ילי",
  creator:"Tom Franz - MasterChef", time:"30 min", serves:"Serves 4",
  video:"https://www.facebook.com/reel/987828117139543",
  intro:"Green shakshuka: spinach braised in cream, soft eggs, stretchy mozzarella, and a kiss of chili heat.",
  needs:["spinach","onion","garlic","cream","mozzarella","eggs","chili"],
  ingredientLines:[
    {text:"3 tbsp olive oil"},
    {text:"2 onions, halved and thinly sliced"},
    {text:"3 garlic cloves, crushed"},
    {text:"200 g baby spinach"},
    {text:"Salt, black pepper, and 1/4 tsp nutmeg"},
    {text:"250 ml heavy cream"},
    {text:"200 g shredded mozzarella"},
    {text:"4-5 eggs"},
    {text:"1 fresh red chili, thinly sliced (optional)"}
  ],
  steps:[
    "Heat the olive oil in a large skillet and cook the onions until soft and translucent. Add the garlic for a minute.",
    "Add the spinach and cover until it wilts down and softens. Season with salt, pepper, and nutmeg.",
    "Pour in the cream and half the mozzarella and stir until the spinach is coated.",
    "Make wells and crack the eggs into them. Cover over low heat for 7-10 minutes — set whites, runny yolks.",
    "Scatter the chili and the rest of the mozzarella, cover for a minute to melt, and serve hot with fresh bread."
  ]
},
{
  id:"46540", diet:"Vegetarian", image:"46540.jpg", category:"Pasta",
  name:"Creamy Mushroom Pasta with Calabrian Chili",
  searchAlias:"פסטת פטריות קרמית עם צ'ילי קלבריאני",
  creator:"Chhaya Joshi", time:"35 min", serves:"Serves 3-4",
  video:"https://www.facebook.com/reel/2968998143310587",
  needs:["pasta","mushrooms","butter","onion","garlic","cream","soy","parmesan","parsley","chili-crisp","cornflour"],
  ingredientLines:[
    {text:"280 g pappardelle"},
    {text:"2 tbsp butter"},
    {text:"450 g mixed mushrooms (portobello + button), sliced"},
    {text:"2-3 tbsp olive oil"},
    {text:"1 shallot or 1/2 onion"},
    {text:"8-10 garlic cloves, crushed"},
    {text:"1 tsp salt, paprika, Italian seasoning + 1/2 tsp chili flakes (optional: pinch of turmeric)"},
    {text:"1 tbsp flour or cornstarch"},
    {text:"1.5 cups pasta water + 1 cup heavy cream"},
    {text:"1 tbsp soy sauce + 1/2 cup Parmesan"},
    {text:"Parsley + Calabrian chili paste (or chili crisp) for drizzling"}
  ],
  steps:[
    "Cook the pasta in salted water, a minute or two short of the package directions.",
    "Sauté the mushrooms in the butter for 5-7 minutes until they start to brown.",
    "Push them aside, add the olive oil, and fry the shallot and garlic for about a minute. Stir everything together.",
    "Over low heat: add the spices and flour and cook for a minute.",
    "Add the pasta water, cream, soy sauce, and Parmesan.",
    "When the sauce thickens — add the pasta and parsley and toss gently.",
    "Drizzle with Calabrian chili and serve with Parmesan and parsley."
  ],
  tips:"From the comments: adding yesterday's roast chicken works great."
},
{
  id:"45154", diet:"Meat", image:"45154.jpg", category:"Soups & Sauces",
  name:"The Trick to Real Thai Curry (Technique)",
  searchAlias:"הטריק לקארי תאילנדי אמיתי (טכניקה)",
  creator:"Cook with Mika", time:"Technique tip",
  video:"https://www.facebook.com/reel/2714945882199393",
  intro:"What they teach in cooking school: don't shake the coconut can! Scoop the fat off the top and fry the curry paste in it.",
  needs:["coconut-milk","curry-red"],
  ingredientLines:[
    {text:"1 can coconut milk/cream — unshaken!"},
    {text:"Curry paste (red/green)"},
    {text:"The rest of your curry ingredients (chicken, vegetables, fish sauce, sugar...)"}
  ],
  steps:[
    "Open the coconut can without shaking it — the thick cream sits on top, the water below.",
    "Scoop the thick cream into a hot pan and fry it until the fat separates ('cracking the cream').",
    "Fry the curry paste in the coconut fat — this is the step that unlocks all the aroma.",
    "Only then add the rest of the coconut liquid and the remaining ingredients and cook as usual.",
    "Bonus: toast whole spices and only then grind them — a game changer for any curry."
  ],
  tips:"From the comments (561 likes): this is why you don't shake the can. You can also just reduce it hard over high heat — same result."
},
{
  id:"46137", diet:"Vegetarian", image:"46137.jpg", category:"Pasta",
  name:"Roasted Red Pepper Pasta",
  searchAlias:"פסטת פלפלים אדומים קלויים",
  creator:"Chhaya Joshi", time:"40 min", serves:"Serves 2-3",
  video:"https://www.facebook.com/reel/1309068421131055",
  intro:"Peppers, onion, and a whole head of garlic roast in the oven and blend with cream cheese into a velvety orange sauce.",
  needs:["pasta","pepper-red","onion","garlic","cream-cheese","tomato-paste","parmesan"],
  ingredientLines:[
    {text:"200 g pasta"},
    {text:"2 red bell peppers, halved"},
    {text:"1/2 onion, halved"},
    {text:"1 whole head of garlic (or 10 cloves)"},
    {text:"Olive oil"},
    {text:"1 tsp salt, 1/2 tsp garlic powder, 1 tsp paprika/cayenne, 1/2 tsp chili flakes"},
    {text:"225 g cream cheese, softened"},
    {text:"2 tbsp tomato paste"},
    {text:"Parmesan and parsley for serving"}
  ],
  steps:[
    "Arrange the peppers, onion, and foil-wrapped garlic head on a baking sheet. Drizzle with olive oil and roast at 200°C for 15-20 minutes until lightly charred.",
    "Cool for 5 minutes and peel the pepper skins.",
    "Cook the pasta in salted water and reserve 1-2 cups of the cooking water.",
    "Blend: cream cheese, the peppers, onion, roasted garlic, the spices, 2 tbsp olive oil, tomato paste, and a cup of pasta water.",
    "Cook the sauce in a skillet for 2-3 minutes until it thickens and deepens in color.",
    "Add the pasta, toss gently, and serve with Parmesan, parsley, and chili flakes."
  ],
  tips:"From the comments: Boursin instead of cream cheese = an upgrade; cottage cheese works too. Adding cooked red lentils to the blender = protein and fiber."
},
{
  id:"45884", diet:"Vegetarian", image:"45884.jpg", category:"Pasta",
  name:"Fettuccine in Tomato Sauce with Burrata",
  searchAlias:"פטוצ'יני ברוטב עגבניות עם בורטה",
  creator:"Sofiaa Foodie", time:"30 min",
  video:"https://www.facebook.com/reel/945938044611949",
  needs:["pasta","canned-tomatoes","garlic","burrata","thyme","parmesan","chili"],
  serves:"Serves 1 (scale up)",
  ingredientLines:[
    {text:"80 g fettuccine (per serving)"},
    {text:"2 garlic cloves, crushed"},
    {text:"200 ml canned chopped tomatoes"},
    {text:"A few sprigs of fresh thyme"},
    {text:"1/2 tsp chili flakes + 1 tsp dried basil"},
    {text:"2 tbsp olive oil"},
    {text:"20 g grated Parmesan"},
    {text:"1 ball of burrata (100-150 g)"},
    {text:"Salt and black pepper"}
  ],
  steps:[
    "Cook the fettuccine in salted water until al dente (8-10 min). Reserve 1/2 cup of the cooking water.",
    "Heat the olive oil in a skillet and fry the garlic for 30-60 seconds until fragrant.",
    "Add the chili flakes, tomatoes, thyme, basil, salt, and pepper — and simmer gently for about 10 minutes until slightly thickened (loosen with pasta water as needed).",
    "Toss the pasta in the sauce with the Parmesan.",
    "Transfer to a plate and set the whole burrata on top. Black pepper, a drizzle of olive oil — and serve."
  ]
},
{
  id:"45458", diet:"Vegetarian", image:"45458.jpg", category:"Soups & Sauces",
  name:"Fridge Jar of Chimichurri",
  searchAlias:"צנצנת צ'ימיצ'ורי למקרר",
  creator:"Ani.beshuk", time:"15 min + resting",
  video:"https://www.facebook.com/reel/988677170482257",
  intro:"Tastiest after a few days of 'resting' in the fridge — perfect for the grill. (Technically closer to salsa criolla — and fantastic on steak.)",
  needs:["parsley","mint","chili","garlic","red-onion","pepper-red","vinegar"],
  ingredientLines:[
    {text:"1 bunch parsley"},
    {text:"A handful of chopped mint leaves"},
    {text:"1 tbsp dried oregano (optional)"},
    {text:"1-2 chili peppers, chopped"},
    {text:"4 garlic cloves, chopped"},
    {text:"1 red onion, chopped"},
    {text:"1/2 red bell pepper + 1/2 yellow bell pepper, finely chopped"},
    {text:"1/4 cup vinegar + 1/4 cup red wine vinegar"},
    {text:"3/4 cup canola oil + 1/4 cup olive oil"},
    {text:"1/2 cup hot water + 1 level tbsp salt"}
  ],
  steps:[
    "Chop all the ingredients — by knife or in a food processor with short pulses. Chunks, not a paste.",
    "Dissolve the salt in half a cup of boiling water and pour into a bowl with the vinegars and oils.",
    "Mix, transfer to an airtight jar, leave out for a day, then refrigerate.",
    "Best made two to three days before the meal."
  ]
},
{
  id:"46428", diet:"Vegetarian", image:"46428.jpg", category:"Pasta",
  name:"5-Ingredient Chili Pasta",
  searchAlias:"פסטת צ'ילי ב-5 מרכיבים",
  creator:"Chhaya Joshi", time:"15 min", serves:"Serves 2",
  video:"https://www.facebook.com/reel/1705848083914281",
  needs:["pasta","butter","garlic","chili-crisp","cream"],
  ingredientLines:[
    {text:"150 g pasta (bucatini)"},
    {text:"1-2 tbsp butter"},
    {text:"7-8 garlic cloves, crushed"},
    {text:"2 heaping tsp chili oil / chili crisp"},
    {text:"3/4 cup heavy cream"},
    {text:"1 tsp salt"},
    {text:"To garnish: more chili oil, parsley, Parmesan"}
  ],
  steps:[
    "Cook the pasta in salted water and reserve a cup of the cooking water.",
    "Butter and garlic over low heat — don't let it burn.",
    "After ~30 seconds, add the chili oil.",
    "Immediately add the cream, stir, and let it thicken (Parmesan helps).",
    "Salt, then the pasta — over medium-low heat so the cream doesn't break.",
    "Loosen with pasta water as needed and serve hot with the garnishes."
  ],
  tips:"From the comments: fantastic next to steak, roasted zucchini, or mushrooms."
},
{
  id:"44813", diet:"Meat", image:"44813.jpg", category:"Chicken",
  name:"Chicken in Onions — Zwiebelhähnchen (Tom Franz)",
  searchAlias:"עוף בבצל — צוויבל הנשן (תום פרנץ)",
  creator:"Tom Franz - MasterChef", time:"2.5 hours", serves:"Serves 6",
  video:"https://www.facebook.com/reel/1263700335890906",
  intro:"His late mother Karin's recipe: 5 ingredients, a sweet-savory caramelized onion sauce, and chicken that falls off the bone. Kosher for Passover.",
  needs:["chicken","onion"],
  ingredientLines:[
    {text:"6 chicken thighs"},
    {text:"1.5 kg onions — halved and thinly sliced"},
    {text:"3 tbsp brown sugar"},
    {text:"Salt and pepper to taste"},
    {text:"3-4 tbsp canola or olive oil"}
  ],
  steps:[
    "Preheat the oven to 180°C.",
    "Spread a little more than half the onions in a baking dish with a bit of oil. Arrange the chicken skin-side down, season with salt, pepper, and brown sugar, cover with the remaining onions and more oil.",
    "Seal with parchment paper + foil and bake for 1.5-2 hours, until the chicken is tender and the onions are caramelized.",
    "Remove the cover, flip the chicken (skin-side up), spoon the juices over, and roast another 25-35 minutes until the skin is golden.",
    "Taste the sauce and balance the salt/pepper/sugar — it should be slightly sweet. Serve with rice or mashed potatoes.",
    "Deep-caramelization tip: you can also do 150°C for 3 hours, covered."
  ]
},
{
  id:"45033", diet:"Vegetarian", image:"45033.jpg", category:"Salads",
  name:"Tzatziki-Bruschetta Dip",
  searchAlias:"מטבל צזיקי-ברוסקטה",
  creator:"Chhaya Joshi", time:"20 min",
  video:"https://www.facebook.com/reel/1287064073395928",
  intro:"A protein-packed layered dip: cold tzatziki on the bottom, tomato salsa on top. With crostini or pita chips.",
  needs:["greek-yogurt","cucumbers","dill","garlic","lemon","tomatoes-fresh","onion","coriander","chili"],
  ingredientLines:[
    {group:"Bruschetta:"},
    {text:"1/4 cup olive oil"},
    {text:"2 small tomatoes, diced + 1/4 onion, chopped"},
    {text:"2 tbsp fresh cilantro + 2 garlic cloves, crushed"},
    {text:"1/2 tsp chili flakes, 1/2 tsp salt, 1/4 tsp pepper"},
    {group:"Tzatziki:"},
    {text:"2 cups Greek yogurt"},
    {text:"2 small cucumbers, grated and drained"},
    {text:"2 tbsp chopped dill + 4 garlic cloves, grated"},
    {text:"Juice of a whole lemon"},
    {text:"1 tsp salt and pepper, 1 tbsp olive oil, 1 tsp vinegar (optional)"}
  ],
  steps:[
    "Make the bruschetta: mix all the ingredients and set aside.",
    "Make the tzatziki: mix all the ingredients (the cucumber grated and well drained).",
    "Spread the tzatziki on a serving plate and pile the bruschetta in the center.",
    "Serve with crostini, pita chips, or crackers."
  ]
},
{
  id:"43988", diet:"Vegetarian", image:"43988.jpg", category:"Pasta",
  name:"Ramen in Spicy Peanut Sauce",
  searchAlias:"ראמן ברוטב בוטנים חריף",
  creator:"Chhaya Joshi", time:"10 min", serves:"Serves 1",
  video:"https://www.facebook.com/reel/1915803359013311",
  needs:["noodles","peanut-butter","chili-crisp","vinegar","soy","scallion","coriander"],
  ingredientLines:[
    {text:"1 pack ramen noodles"},
    {text:"2 tbsp peanut butter"},
    {text:"1-1.5 tbsp chili oil"},
    {text:"1 tbsp rice vinegar"},
    {text:"1.5 tbsp soy sauce + pinch of salt"},
    {text:"1 tbsp scallions + 1 tbsp cilantro"},
    {text:"1.5-2 cups of the noodle cooking water"},
    {text:"To garnish: chili oil and black sesame seeds"}
  ],
  steps:[
    "Cook the ramen one minute short of the package directions and reserve ~2 cups of the cooking water.",
    "In a skillet: peanut butter, chili oil, rice vinegar, soy sauce + 1.5-2 cups of hot noodle water. Stir.",
    "When the sauce boils, add the noodles — it thickens within 1-2 minutes.",
    "Garnish with black sesame, chili oil, cilantro, and scallions. Serve fast — the noodles soak up the sauce."
  ]
},
{
  id:"48304", diet:"Vegetarian", image:"48304.jpg", category:"Soups & Sauces",
  name:"Hungarian Mushroom Soup",
  searchAlias:"מרק פטריות הונגרי",
  creator:"Chhaya Joshi", time:"40 min", serves:"Serves 4",
  video:"https://www.facebook.com/reel/857035817371044",
  intro:"The mushroom soup from the Moosewood vegetarian cookbook: dill, sweet paprika, and soy sauce — creamy and warming.",
  needs:["butter","onion","mushrooms","dill","garlic","lemon","stock","soy","milk","sour-cream","parsley"],
  ingredientLines:[
    {text:"4 tbsp butter"},
    {text:"1.5 cups chopped white onion"},
    {text:"450 g sliced mushrooms"},
    {text:"2 tsp dried dill + 1 tsp dried thyme"},
    {text:"1 tbsp sweet paprika + 1 tbsp lemon juice"},
    {text:"2 garlic cloves, grated"},
    {text:"2.5 cups vegetable (or chicken) stock"},
    {text:"2 tbsp soy sauce"},
    {text:"3 tbsp flour + 1 cup milk or half-and-half"},
    {text:"1/3 cup sour cream (optional) + 3 tbsp parsley"}
  ],
  steps:[
    "Melt the butter in a pot, sauté the onion for a few minutes, and add the mushrooms. Cook 8-10 minutes over medium heat.",
    "Add the dill, thyme, paprika, garlic, and lemon juice for 2 minutes. Add the stock and soy sauce and cook a few minutes.",
    "Whisk the flour into the milk until lump-free and add while stirring. Cook until thickened — do not boil!",
    "Finish with the sour cream (optional), parsley, and warm bread on the side."
  ],
  tips:"From the comments: roast the mushrooms in the oven (200°C, 30 min) with shallot, brown butter, and white wine = double the depth."
},
{
  id:"67745", diet:"Vegetarian", image:"67745.jpg", category:"Pasta",
  name:"'Homemade Michelin' Garlic-Cream Spaghetti",
  searchAlias:"ספגטי שום-שמנת 'מישלן ביתי'",
  creator:"Feeedmi · Disha Nayak", time:"20 min",
  video:"https://www.facebook.com/reel/1789266455757372",
  intro:"Reconstructed from the video: garlic infused in olive oil, a pasta-water and Parmesan emulsion, and lots of black pepper.",
  needs:["pasta","garlic","cream","parmesan","parsley"],
  ingredientLines:[
    {text:"Spaghetti"},
    {text:"Olive oil"},
    {text:"Garlic cloves (whole, to be removed, or sliced)"},
    {text:"A splash of cream + cooking water"},
    {text:"Grated Parmesan"},
    {text:"Freshly ground black pepper (be generous!) + parsley"}
  ],
  steps:[
    "Gently fry the garlic in olive oil over low heat — no browning (the Italian trick: whole cloves you fish out after a minute).",
    "Add a ladle of pasta water and a splash of cream and let the sauce come together.",
    "Add al dente spaghetti and toss.",
    "Off the heat: Parmesan, stirring vigorously until creamy.",
    "Finish with plenty of black pepper (lightly toasted is best) and parsley."
  ]
},
{
  id:"68238", diet:"Meat", image:"68238.jpg", category:"Chicken",
  name:"Giraffe's Satay Sauce (over Schnitzel)",
  searchAlias:"רוטב סאטה של ג'ירף (על שניצל)",
  creator:"Dana Reicher Moyal", time:"10 min",
  video:"https://www.facebook.com/reel/1038135132524394",
  intro:"A re-creation of Giraffe's legendary satay dish — with a modern kick of chili crunch. Pour over hot schnitzel next to rice.",
  needs:["curry-red","peanut-butter","coconut-milk","honey-silan","chili-crisp","scallion","peanuts","sesame-oil","chicken"],
  ingredientLines:[
    {group:"Sauce:"},
    {text:"1/2 tbsp red curry paste"},
    {text:"4 tbsp peanut butter (smooth is best)"},
    {text:"1/2 tsp yellow curry powder"},
    {text:"1 cup coconut cream"},
    {text:"Pinch of salt + a little honey"},
    {text:"1 tsp chili crunch — the addition that changes everything"},
    {group:"On top:"},
    {text:"Chopped scallions, peanuts, a handful of furikake, and a touch of sesame oil"},
    {text:"To serve: hot schnitzel and rice"}
  ],
  steps:[
    "Bring all the sauce ingredients to a boil in a small pot over medium heat until thickened.",
    "Pour over the schnitzel, scatter scallions, peanuts, and furikake, and finish with sesame oil.",
    "Tip: don't overheat — the peanut butter can split."
  ]
},
{
  id:"68240", diet:"Meat", image:"68240.jpg", category:"Chicken",
  name:"Thai Cashew Chicken",
  searchAlias:"עוף קשיו תאילנדי",
  creator:"Don't Go Bacon My Heart", time:"30 min",
  video:"https://www.facebook.com/reel/979491511767379",
  intro:"A restaurant-style stir-fry from super simple ingredients — crispy chicken, toasted cashews, and a glossy sauce.",
  needs:["chicken","cashews","pepper-red","onion","garlic","scallion","chili","soy","hoisin"],
  serves:"Serves 4",
  ingredientLines:[
    {text:"600 g boneless chicken thighs, cubed"},
    {text:"1 tsp white pepper + 2 tsp soy sauce (for the marinade)"},
    {text:"50 g flour (for coating)"},
    {text:"120 ml oil for frying"},
    {text:"200 g unsalted cashews"},
    {text:"2 white onions, roughly chopped"},
    {text:"2 bell peppers (red + green), diced"},
    {text:"4 garlic cloves, chopped + 2 red chilies, sliced"},
    {text:"3 scallions (whites and greens separated), in 2.5 cm pieces"},
    {text:"1.5 tbsp sugar + 1 tbsp oyster sauce + 1 tbsp soy sauce"},
    {text:"Rice for serving"}
  ],
  steps:[
    "Mix the chicken with the white pepper and 2 tsp soy sauce, then coat well in flour.",
    "Heat the oil in a wok and fry the cashews to a deep gold (watch them!). Remove.",
    "In two batches: shake off excess flour and fry the chicken until crispy and golden (~5 min per batch). Remove and pour off most of the oil (keep ~2 tbsp).",
    "Stir-fry the peppers, onion, and garlic for 2 minutes; add the chilies and the scallion whites for a minute.",
    "Return the chicken, add the sugar, oyster sauce, and soy sauce. Add the cashews and the scallion greens.",
    "Serve immediately over rice, while everything is hot and crispy."
  ]
},
{
  id:"68242", diet:"Meat", image:"68242.jpg", category:"Chicken",
  name:"Black Pepper Chicken — 20 Minutes",
  searchAlias:"עוף בפלפל שחור — 20 דקות",
  creator:"foodinfivemins", time:"20 min", serves:"Serves 3 (623 calories, 46 g protein)",
  video:"https://www.facebook.com/reel/1076556568205556",
  needs:["chicken","garlic","onion","pepper-red","stock","honey-silan","hoisin","chili","scallion","vinegar","sesame-oil","soy","rice"],
  ingredientLines:[
    {text:"600 g boneless chicken thighs, cubed"},
    {text:"2 garlic cloves + 1/2 onion"},
    {text:"1 red bell pepper + 1 green bell pepper"},
    {text:"100 ml chicken stock"},
    {text:"2 tbsp honey + 3 tbsp oyster sauce"},
    {text:"1 heaping tsp coarsely ground black pepper"},
    {text:"1 fresh chili + 2 scallions"},
    {text:"1 tbsp rice vinegar + 1 tbsp sesame oil + 1 tbsp dark soy sauce"},
    {text:"250 g rice (for serving)"}
  ],
  steps:[
    "Sear the chicken cubes in a hot skillet.",
    "Add the garlic, onion, and peppers and stir-fry.",
    "Mix the sauce: stock, honey, oyster sauce, black pepper, vinegar, sesame oil, and soy — and pour it in.",
    "Reduce to a glossy sauce that coats everything.",
    "Finish with fresh chili and scallions. Serve over rice (great for meal prep)."
  ],
  tips:"From the comments: no oyster sauce? Hoisin or mushroom sauce. Adding cashews is an upgrade."
},
{
  id:"68319", diet:"Meat", image:"68319.jpg", category:"Chicken",
  name:"Marry Me Chicken Pasta",
  searchAlias:"פסטת 'תתחתני איתי' עם עוף (Marry Me)",
  creator:"Vivaldi Restaurant", time:"30 min",
  video:"https://www.facebook.com/reel/1487781258988434",
  intro:"Reconstructed from the video (the chef keeps his spice blend a secret): seared chicken in a sun-dried tomato cream sauce.",
  needs:["chicken","garlic","tomatoes-fresh","cream","parmesan","pasta","basil","stock"],
  ingredientLines:[
    {text:"Chicken breast pieces, seasoned (salt, pepper, paprika)"},
    {text:"Olive oil + 1 crushed garlic clove"},
    {text:"Sun-dried tomatoes in oil, chopped"},
    {text:"Chicken stock (to deglaze the pan)"},
    {text:"Heavy cream + Parmesan"},
    {text:"Chili flakes + basil"},
    {text:"Pasta cooked al dente"}
  ],
  steps:[
    "Sear the seasoned chicken until golden and remove.",
    "In the same pan: garlic and sun-dried tomatoes for a minute.",
    "Pour in the stock and scrape up the browned bits; add the cream and Parmesan for a pink, creamy sauce.",
    "Return the chicken and cook through.",
    "Add the pasta, toss, and finish with basil."
  ]
},
{
  id:"68322", diet:"Meat", image:"68322.jpg", category:"Chicken",
  name:"Cowboy Butter Chicken with Mash & Broccolini",
  searchAlias:"עוף חמאת קאובוי עם פירה וברוקוליני",
  creator:"foodinfivemins", time:"30 min", serves:"Serves 3 (605 calories, 50 g protein)",
  video:"https://www.facebook.com/reel/2444509202712469",
  needs:["chicken","onion","worcester","butter","mustard","stock","garlic","parsley","lemon","broccoli","potato","milk"],
  ingredientLines:[
    {group:"Chicken:"},
    {text:"700 g chicken thighs, cubed"},
    {text:"1 small onion + 4 garlic cloves"},
    {text:"1 tbsp Italian herb blend + 1 tbsp cayenne (less if sensitive)"},
    {text:"2 tbsp Worcestershire sauce"},
    {text:"30 g butter + 2 tbsp Dijon mustard"},
    {text:"75 ml chicken stock"},
    {text:"1/2 handful parsley + 1 lemon"},
    {group:"Sides:"},
    {text:"1 large bunch broccolini"},
    {text:"700 g potatoes + 25 g butter + 40 ml milk (for the mash)"}
  ],
  steps:[
    "Season the chicken cubes with the herbs and cayenne and sear.",
    "Add the onion and garlic and sauté.",
    "Add the butter, Worcestershire, Dijon, and stock — reduce to a glossy 'cowboy butter' sauce.",
    "Finish with parsley and lemon juice.",
    "Mash: boil the potatoes and mash with butter and milk. Broccolini: a quick blanch/steam.",
    "Assemble boxes/plates: mash, broccolini, and the chicken with its sauce."
  ]
},
{
  id:"68382", diet:"Meat", image:"68382.jpg", category:"Chicken",
  name:"One-Pot Hainanese Chicken & Rice (Douglas Chau)",
  searchAlias:"עוף האינאן עם אורז — סיר אחד (Douglas Chau)",
  creator:"Douglas Chau", time:"40 min", serves:"Serves 2",
  video:"https://www.facebook.com/reel/884239044756802",
  intro:"The dish that won a 19-contestant one-pot competition on Food Network. 80% of the result with 20% of the work.",
  needs:["chicken","rice","garlic","ginger","scallion","stock","sesame-oil","sriracha","lime","cucumbers","coriander"],
  ingredientLines:[
    {text:"2 boneless chicken thighs (450 g) + 2 tsp sesame oil + 1/4 tsp salt"},
    {group:"Rice:"},
    {text:"1 cup jasmine rice, 6 garlic cloves, 1/2 thumb of ginger, 2 scallions"},
    {text:"1.25 cups chicken stock + 1 tsp bouillon powder + 1/2 tsp turmeric"},
    {group:"Ginger-scallion sauce:"},
    {text:"Ginger + scallions + salt + 1 tsp sesame oil, topped with 2 tbsp sizzling-hot neutral oil"},
    {group:"Chili-garlic sauce:"},
    {text:"6 garlic cloves, ginger, 2 tbsp sambal, 2 tbsp sriracha, 1 tbsp stock, 1 tsp lime juice, 2 tsp sugar"},
    {text:"On the side: cucumber, cilantro, scallions"}
  ],
  steps:[
    "Season the chicken with the sesame oil and salt.",
    "In a pot: rice, garlic, ginger, scallions, stock, bouillon powder, and turmeric. Lay the chicken on top of the rice.",
    "Bring to a boil, lower to a gentle simmer, cover for 20 minutes until the liquid is absorbed.",
    "The ginger sauce: pour the sizzling oil over the ginger-scallion mixture — it should sizzle — and stir.",
    "The chili sauce: just mix everything together.",
    "Slice the chicken, let the rice rest for 10 minutes, and serve with both sauces, cucumber, and cilantro."
  ]
},
{
  id:"68384", diet:"Meat", image:"68384.jpg", category:"Chicken",
  name:"Rice-Cooker Hainanese Chicken (The Lazy Version)",
  searchAlias:"עוף האינאן בסיר אורז (הגרסה העצלנית)",
  creator:"Douglas Chau", time:"One cook cycle", serves:"Serves 3-4",
  video:"https://www.facebook.com/reel/1567731744756611",
  intro:"The same dish — at the press of a button: everything into the rice cooker, chicken on top, and both sauces made in the meantime.",
  needs:["chicken","rice","garlic","ginger","scallion","stock","sesame-oil","sriracha","lime","cucumbers","coriander"],
  ingredientLines:[
    {text:"2 chicken thighs (450 g) + 2 tsp sesame oil + 1/4 tsp salt"},
    {text:"Ginger-garlic rice: 2 cups jasmine rice, 3 garlic cloves, ginger, 3 scallions, 2 cups stock, 1 tsp bouillon powder, 1/2 tsp turmeric"},
    {text:"Ginger-scallion oil: 2 tbsp sizzling-hot neutral oil over ginger, scallions, sesame oil, and salt"},
    {text:"Chili-garlic sauce: 2 tbsp sriracha, 2 tbsp sambal, 6 garlic cloves, ginger, 1 tbsp stock, 1 tsp lime juice, 2 tsp sugar"},
    {text:"On the side: cucumber, cilantro, scallions"}
  ],
  steps:[
    "Put all the rice ingredients in the rice cooker, arrange the seasoned chicken on top, and run a regular cook cycle.",
    "Meanwhile, make both sauces (hot oil over the ginger-scallions; the chili sauce is just stirred together).",
    "Slice, build a bowl with the rice, chicken, sauces, and sides."
  ],
  tips:"The full recipe with step videos: thefoodie.menu (access code ginger)."
},
{
  id:"68434", diet:"Vegetarian", image:"68434.jpg", category:"Soups & Sauces",
  name:"Creamy 3-Tomato Sauce (Viral)",
  searchAlias:"רוטב 3 העגבניות הקרמי (ויראלי)",
  creator:"Comidas Caseras", time:"20 min",
  video:"https://www.facebook.com/reel/1594274705391563",
  intro:"Reconstructed from the viral video (1.5 million likes): seared tomatoes mashed into a rich sauce with a touch of cream.",
  needs:["tomatoes-fresh","garlic","tomato-paste","cream","pasta"],
  ingredientLines:[
    {text:"3 ripe tomatoes, halved"},
    {text:"Olive oil"},
    {text:"2-3 garlic cloves"},
    {text:"1-2 tbsp tomato paste"},
    {text:"Oregano (or basil — better, per the comments!)"},
    {text:"A splash of cream"},
    {text:"Salt; pasta or rice for serving"}
  ],
  steps:[
    "Sear the tomato halves cut-side down in olive oil until charred and softened.",
    "Add the garlic, tomato paste, oregano, and salt.",
    "Mash the tomatoes into a sauce, add a splash of cream, and cook a few minutes.",
    "Serve over pasta (or with shrimp sautéed in the same oil — a tip from the comments)."
  ]
},
{
  id:"68607", diet:"Meat", image:"68607.jpg", category:"Chicken",
  name:"Teriyaki Chicken with Fried Rice",
  searchAlias:"עוף טריאקי עם אורז מוקפץ",
  creator:"FOODY", time:"45 min + marinating", serves:"Serves 4-5",
  video:"https://www.facebook.com/reel/894389426489127",
  needs:["chicken","teriyaki","soy","sesame-oil","rice","garlic","eggs","ginger","sprouts","scallion"],
  ingredientLines:[
    {group:"Teriyaki chicken:"},
    {text:"500 g chicken breast, cubed"},
    {text:"1 cup teriyaki sauce + 1/4 cup sweet soy sauce + 4 tbsp sesame oil"},
    {group:"Fried rice:"},
    {text:"500 g cooked, cold white rice (day-old is best) + 1 tsp salt"},
    {text:"6 garlic cloves, sliced + 1 tbsp chopped ginger"},
    {text:"5 eggs"},
    {text:"500 g bean sprouts + a bunch of scallions cut into batons"},
    {text:"1/2 cup canola oil + 1/4 cup sesame oil"},
    {text:"1/2 cup soy sauce + 1/3 cup sweet soy sauce"},
    {text:"Black sesame seeds for serving"}
  ],
  steps:[
    "Marinate the chicken cubes in the teriyaki, sweet soy, and sesame oil — overnight in the fridge.",
    "Cook the rice with salt and cool it completely (a day ahead is best).",
    "Broiler on maximum heat (~250°C): roast the chicken (on skewers or not) ~12 minutes until browned.",
    "In a large, scorching-hot skillet: both oils, lightly beaten eggs, then garlic, ginger, and scallions for a minute.",
    "Add the cold rice, mix well, then both soy sauces until the rice is hot and seasoned.",
    "Sprouts in, one final toss, and off the heat. Serve with the chicken on top and black sesame."
  ]
},
{
  id:"68882", diet:"Vegetarian", image:"68882.jpg", category:"Pasta",
  name:"Creamy Zucchini Pasta (Vivaldi)",
  searchAlias:"פסטת קישואים קרמית (Vivaldi)",
  creator:"Vivaldi Restaurant", time:"30 min",
  video:"https://www.facebook.com/reel/1126705485620761",
  intro:"In the style of Stanley Tucci's famous zucchini: the secret is frying the zucchini slowly until partly caramelized.",
  needs:["pasta","zucchini","garlic","basil","parmesan"],
  ingredientLines:[
    {text:"Spaghetti or long pasta"},
    {text:"3-4 zucchini, thinly sliced"},
    {text:"A generous amount of olive oil"},
    {text:"2-3 garlic cloves"},
    {text:"Basil (+ mint — a Greek twist from the comments)"},
    {text:"Parmesan + cooking water"},
    {text:"Salt and pepper"}
  ],
  steps:[
    "Fry the zucchini slices slowly in olive oil until soft and golden — the partial caramelization is the secret.",
    "Add the garlic and lightly mash the zucchini.",
    "Add al dente spaghetti, cooking water, and Parmesan and toss into a creamy sauce.",
    "Finish with basil/mint, salt, and pepper."
  ],
  tips:"From the comments: lemon zest + toasted breadcrumbs on top; or toasted almonds/pine nuts."
},
{
  id:"68884", diet:"Vegetarian", image:"68884.jpg", category:"Salads",
  name:"German Potato & Cucumber Salad (Kartoffel-Gurkensalat)",
  searchAlias:"סלט תפו\"א ומלפפונים גרמני (Kartoffel-Gurkensalat)",
  creator:"German Mom Kitchen", time:"40 min", serves:"Serves 6",
  video:"https://www.facebook.com/reel/1334162438828186",
  intro:"The taste of a German summer: warm potatoes, fresh cucumber, and a vinegar-mustard dressing with hot stock. Perfect for a barbecue.",
  needs:["potato","cucumbers","red-onion","dill","vinegar","mustard","stock"],
  ingredientLines:[
    {text:"1 kg waxy potatoes (not starchy)"},
    {text:"1 cucumber"},
    {text:"1 small red onion or shallot"},
    {text:"Fresh chives or dill"},
    {group:"Dressing:"},
    {text:"5 tbsp light vinegar + 6 tbsp oil"},
    {text:"1 tsp mustard + 1 tsp sugar"},
    {text:"100 ml hot vegetable stock"},
    {text:"Salt and black pepper"}
  ],
  steps:[
    "Boil the potatoes until tender and slice them while still warm.",
    "Thinly slice the cucumber and onion.",
    "Mix the hot stock with the vinegar, mustard, sugar, salt, and pepper.",
    "Pour over the warm potatoes and let them soak for a few minutes.",
    "Add the oil and mix gently.",
    "Fold in the cucumber, onion, and herbs. Let it rest before serving."
  ],
  tips:"From the comments: a version with liquid cream instead of oil + red wine vinegar; caraway seeds in the cooking water."
},
{
  id:"68885", diet:"Meat", image:"68885.jpg", category:"Chicken",
  name:"Coconut Red Curry Chicken (Foodie.Randy)",
  searchAlias:"קארי אדום עוף וקוקוס (Foodie.Randy)",
  creator:"Foodie.Randy", time:"35 min", serves:"Serves 2-3",
  video:"https://www.facebook.com/reel/1807917543983966",
  needs:["chicken","onion","garlic","ginger","curry-red","coconut-milk","stock","fish-sauce","pepper-red","lime","basil","rice"],
  ingredientLines:[
    {text:"680 g boneless chicken thighs, in pieces"},
    {text:"1 tbsp neutral oil"},
    {text:"1/2 onion, thinly sliced"},
    {text:"3 garlic cloves, crushed + 1 tbsp grated ginger"},
    {text:"3 tbsp red curry paste"},
    {text:"1 can (400 ml) coconut milk"},
    {text:"1/2 cup chicken stock or water"},
    {text:"1 tbsp fish sauce + 1 tbsp brown sugar"},
    {text:"1 red bell pepper, sliced"},
    {text:"1-2 tsp lime juice"},
    {text:"Basil/cilantro, scallions, and jasmine rice for serving"}
  ],
  steps:[
    "Pat the chicken dry and salt it; sear 3-4 minutes per side until browned (not cooked through) and remove.",
    "Over medium heat: onion for 2-3 minutes; garlic and ginger for 30 seconds.",
    "Fry the curry paste for a minute, stirring.",
    "Pour in a third of the coconut milk and let it bubble 1-2 minutes; add the rest + the stock.",
    "Fish sauce and brown sugar; return the chicken, add the pepper, and simmer gently 8-10 minutes, uncovered.",
    "Off the heat: lime juice. Balance (salty/sweet/sour) and serve over jasmine rice."
  ]
},
{
  id:"68886", diet:"Meat", image:"68886.jpg", category:"Soups & Sauces",
  name:"Cheater's Kubbeh — Beet Soup with Beef-Semolina Meatballs",
  searchAlias:"קובה בלוף — מרק סלק עם קציצות בשר וסולת",
  creator:"Liza Panelim", time:"1 hour",
  video:"https://www.facebook.com/reel/1540152123759967",
  intro:"All the flavor of beet kubbeh soup — without the rolling: simple beef-semolina meatballs instead of kubbeh dumplings.",
  needs:["beef","semolina","beets","onion","garlic","lemon","coriander","eggs","tomato-paste"],
  ingredientLines:[
    {group:"Soup:"},
    {text:"4 small raw beets, in 1 cm cubes (or coarsely grated)"},
    {text:"1 large white onion, diced + 2-3 celery stalks with leaves"},
    {text:"1 tbsp pomegranate molasses + 1 tbsp baharat/ras el hanout + 1 tbsp salt"},
    {text:"Seasoned water: 2 liters water, 2 crushed garlic cloves, 1 tbsp lemon zest, juice of a juicy lemon"},
    {group:"Semolina dough:"},
    {text:"1 cup semolina + 1 cup boiling water + 1/2 tsp salt + 2 tbsp olive oil"},
    {group:"Meatballs:"},
    {text:"1/2 kg ground meat (beef/turkey/chicken thigh, or a vegetarian ground substitute)"},
    {text:"All of the semolina dough"},
    {text:"1 small white onion, finely chopped + 1 cup chopped cilantro leaves"},
    {text:"1 egg, 1 heaping tsp salt, 1 tsp baharat, 1 tsp tomato paste, 2 tbsp olive oil"}
  ],
  steps:[
    "Preheat the oven to 190°C.",
    "The semolina dough: mix the semolina, boiling water, oil, and salt and let it rest about 5 minutes.",
    "The soup: in a quarter cup of olive oil, cook the onion, celery, and beets about 10 minutes without liquid, stirring. Add the seasoned water, bring to a boil, cover, and lower the heat.",
    "The meatballs: mix the semolina dough with the meat, onion, cilantro, egg, and seasonings — and knead really well (the kneading step is critical).",
    "With wet hands, form tight, uniform meatballs on a parchment-lined baking sheet and bake for 20 minutes to firm up.",
    "Slide the meatballs into the soup only once they are cool and firm (otherwise they fall apart). Raise the heat and cook 15 minutes, uncovered.",
    "Taste and adjust — more lemon or salt as needed. Serve with white rice."
  ],
  tips:"From the comments: you can flatten the mixture, freeze it slightly, and cut it into cubes — 'geometric meatballs'."
},
{
  id:"68893", diet:"Meat", image:"68893.jpg", category:"Beef",
  name:"German Farmer's Stew (Bauerneintopf)",
  searchAlias:"תבשיל האיכרים הגרמני (Bauerneintopf)",
  creator:"German Mom Kitchen", time:"45 min", serves:"Serves 4",
  video:"https://www.facebook.com/reel/1891034631584322",
  intro:"One pot that has warmed German kitchens for generations: ground beef, potatoes, and vegetables in a tomato-paprika sauce.",
  needs:["beef","potato","carrots","pepper-red","onion","tomato-paste","canned-tomatoes","stock","parsley","sour-cream"],
  ingredientLines:[
    {text:"500 g ground beef"},
    {text:"500 g potatoes, cubed"},
    {text:"2 carrots, sliced"},
    {text:"1 red bell pepper, diced + 1 onion, chopped"},
    {text:"2 tbsp tomato paste"},
    {text:"400 g crushed tomatoes"},
    {text:"300 ml stock"},
    {text:"1 tsp paprika, pinch of sugar, salt and pepper"},
    {text:"2 tbsp parsley + a spoonful of sour cream for serving"}
  ],
  steps:[
    "Brown the ground beef in a large pot.",
    "Add the onion for 2-3 minutes, then the tomato paste.",
    "Add the potatoes, carrots, pepper, tomatoes, and stock.",
    "Season with the paprika, sugar, salt, and pepper.",
    "Simmer gently for 20-25 minutes until the potatoes are tender.",
    "Stir in the parsley and serve with a spoonful of sour cream."
  ],
  tips:"From the comments: a vegetarian version with lentils instead of the beef works great."
},
{
  id:"68894", diet:"Vegetarian", image:"68894.jpg", category:"Pasta",
  name:"Porcini & Truffle Fettuccine (Tre Lune)",
  searchAlias:"פטוצ'יני פורצ'יני וכמהין (Tre Lune)",
  creator:"Tre Lune Restaurant", time:"25 min",
  video:"https://www.facebook.com/reel/1043622271384930",
  intro:"Reconstructed from the Hollywood restaurant's video: porcini mushrooms, garlic, butter, and the aroma of black truffle.",
  needs:["pasta","mushrooms","garlic","butter","parsley","parmesan","truffle"],
  ingredientLines:[
    {text:"Fettuccine"},
    {text:"300 g porcini mushrooms (or a mushroom mix + soaked dried porcini)"},
    {text:"2 garlic cloves, smashed"},
    {text:"Butter + olive oil"},
    {text:"Chopped parsley"},
    {text:"Parmesan + a splash of cream or extra butter"},
    {text:"Truffle paste/oil to taste"},
    {text:"Cooking water, salt, and pepper"}
  ],
  steps:[
    "Sauté the porcini with the garlic in butter and olive oil until golden.",
    "Add the parsley and a ladle of cooking water.",
    "Add the al dente fettuccine and toss.",
    "Parmesan and more butter (or a splash of cream) for a glossy sauce.",
    "Off the heat: truffle to taste. Serve immediately."
  ]
}
);
