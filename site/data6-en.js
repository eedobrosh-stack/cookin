/* Cookin — batch 6 (2026-09-11): 46 dishes synced from Eedo's "GeverGever" WhatsApp group (Aug 2025 – Mar 2026) — English */

Object.assign(INGREDIENTS, {
  peach:              {label:"Peaches", group:"Vegetables & Fruit", subs:[]},
  sage:               {label:"Sage", group:"Herbs", subs:["thyme"]},
  balsamic:           {label:"Balsamic vinegar", group:"Pantry & Canned", subs:["vinegar"]},
  feta:               {label:"Feta / Bulgarian cheese", group:"Dairy", subs:["mozzarella"]},
  ricotta:            {label:"Ricotta", group:"Dairy", subs:["cream-cheese"]},
  artichoke:          {label:"Artichoke (jarred)", group:"Pantry & Canned", subs:[]},
  "sundried-tomatoes":{label:"Sun-dried tomatoes", group:"Pantry & Canned", subs:["cherry-tomatoes"]},
  dates:              {label:"Dates", group:"Vegetables & Fruit", subs:["honey-silan"]},
  corn:               {label:"Corn", group:"Vegetables & Fruit", subs:[]},
  chickpeas:          {label:"Chickpeas (canned)", group:"Pantry & Canned", subs:[]},
  chard:              {label:"Chard / kale", group:"Vegetables & Fruit", subs:["spinach"]},
  cabbage:            {label:"White cabbage", group:"Vegetables & Fruit", subs:["cabbage-napa"]},
  "curry-powder":     {label:"Curry powder", group:"Pantry & Canned", subs:["curry-yellow"]},
  sesame:             {label:"Sesame seeds", group:"Asian Pantry", subs:[]},
  ravioli:            {label:"Ravioli (fresh)", group:"Pantry & Canned", subs:["pasta"]},
  bread:              {label:"Bread / baguette / challah", group:"Pantry & Canned", subs:[]},
  saffron:            {label:"Saffron", group:"Pantry & Canned", subs:["turmeric"]},
  marzipan:           {label:"Marzipan", group:"Pantry & Canned", subs:[]},
  "sweet-chili":      {label:"Sweet chili sauce", group:"Asian Pantry", subs:["sriracha"]},
  "rose-petals":      {label:"Edible dried roses", group:"Pantry & Canned", subs:[]}
});

RECIPES.push(
{
  id:"29043", diet:"Vegetarian", image:"29043.jpg", category:"Pasta",
  name:"Orecchiette with Cherry Tomatoes and Broccoli", searchAlias:"אורקייטה עם עגבניות שרי וברוקולי",
  creator:"Haim Cohen", time:"25 min", serves:"Serves 3-4",
  video:"https://www.facebook.com/reel/1327799658984345",
  intro:"Short pasta cooked together with the broccoli stem, and a cherry tomato and garlic sauce built in a cold pan over low heat. The broccoli stays tender but whole, and Parmigiano finishes the dish.",
  needs:["pasta","cherry-tomatoes","broccoli","olive-oil","garlic","sage","tomato-paste","salt","parmesan"],
  ingredientLines:[
    {text:"250 g short pasta (orecchiette or similar)", qty:250, unit:"g", name:"short pasta", prep:"orecchiette or similar"},
    {text:"500 g cherry tomatoes, halved", qty:0.5, unit:"kg", name:"cherry tomatoes", prep:"halved"},
    {text:"1 broccoli stem, thinly sliced", qty:1, unit:"", name:"broccoli stem", prep:"thinly sliced"},
    {text:"the florets", qty:null, unit:"", name:"broccoli florets"},
    {text:"2-3 tablespoons olive oil", qty:3, unit:"tbsp", name:"olive oil", qtyText:"2-3"},
    {text:"2 garlic cloves, sliced", qty:2, unit:"clove", name:"garlic", prep:"sliced"},
    {text:"2 sage leaves", qty:2, unit:"", name:"sage", prep:"leaves"},
    {text:"1 tablespoon tomato paste diluted in 2 tablespoons water", qty:1, unit:"tbsp", name:"tomato paste", prep:"diluted in 2 tbsp water"},
    {text:"Salt for the pasta water", qty:null, unit:"", name:"salt", prep:"for the pasta water"},
    {text:"Parmigiano to serve", qty:null, unit:"", name:"parmigiano", prep:"to serve"}
  ],
  steps:[
    "Bring a large pot of water with a generous handful of salt to a boil. Add the pasta and the sliced broccoli stem.",
    "About 5 minutes before the pasta is done, add the florets. Cook until the pasta is al dente and the broccoli is soft but intact.",
    "In a cold pan, put the olive oil, sliced garlic and cherry tomatoes. Turn on low heat and let the garlic fry gently.",
    "Raise the heat, add the diluted tomato paste and the sage leaves.",
    "Drain the pasta and broccoli together, transfer to the pan with the sauce, toss, plate and shower with fresh Parmigiano."
  ],
  tips:"Cooking the broccoli stem with the pasta saves a pot and softens it exactly on time."
},
{
  id:"29154", diet:"Vegetarian", image:"29154.jpg", category:"Soups & Sauces",
  name:"Olive Oil and Cherry Tomato Dip", searchAlias:"מטבל שמן זית ועגבניות שרי",
  creator:"Tom Franz", time:"15 min", serves:"Serves 4-6",
  video:"https://www.facebook.com/reel/1409473880570649",
  intro:"An Italian dip for easy entertaining: cherry tomatoes, basil, Parmesan and chili swimming in olive oil and balsamic. Crush lightly and spread on bruschetta or toasted challah. Keep the leftover oil for a salad or an omelette.",
  needs:["olive-oil","cherry-tomatoes","basil","parmesan","chili","salt","balsamic","garlic","bread"],
  ingredientLines:[
    {text:"¾-1 cup olive oil", qty:1, unit:"cup", name:"olive oil", qtyText:"3/4-1"},
    {text:"300 g cherry tomatoes, halved", qty:300, unit:"g", name:"cherry tomatoes", prep:"halved"},
    {text:"A handful of fresh basil leaves, chopped", qty:1, unit:"handful", name:"basil", prep:"fresh leaves, chopped"},
    {text:"50 g grated Parmesan", qty:50, unit:"g", name:"parmesan", prep:"grated"},
    {text:"Chili flakes, to taste", qty:null, unit:"", name:"chili flakes", prep:"to taste"},
    {text:"Salt, to taste", qty:null, unit:"", name:"salt", prep:"to taste"},
    {text:"1-2 tablespoons good balsamic vinegar", qty:2, unit:"tbsp", name:"balsamic vinegar", prep:"good quality", qtyText:"1-2"},
    {text:"2 garlic cloves, crushed", qty:2, unit:"clove", name:"garlic", prep:"crushed"},
    {text:"To serve: bruschetta / toasted challah / good bread", qty:null, unit:"", name:"bruschetta / toasted challah / bread", prep:"to serve"}
  ],
  steps:[
    "Pour the olive oil into a bowl, add the cherry tomatoes and stir lightly.",
    "Add the chopped basil, crushed garlic, Parmesan, chili, salt and balsamic. Stir gently.",
    "Let the dip rest about 10 minutes at room temperature for the flavors to meld, and serve with toasted bread."
  ],
  tips:"In Italy the tomatoes are lightly crushed and spread on bruschetta. The leftover oil is great for a salad dressing, an omelette or a pasta sauce base."
},
{
  id:"29242", diet:"Vegetarian", image:"29242.jpg", category:"Pasta",
  name:"Tali Bar's Light Vegetable Pasta", searchAlias:"פסטה ירקות קלילה של טלי בר",
  creator:"Tali Bar", time:"30 min", serves:"Serves 4",
  video:"https://www.facebook.com/reel/3091777217657436",
  intro:"Penne with lots of finely diced vegetables: carrot, celery, cauliflower, zucchini, cherry tomatoes, Kalamata olives and herbs, roasted in the pan and sauced with pasta water and lemon zest.",
  needs:["pasta","onion","carrots","celery","cauliflower","chili","zucchini","garlic","cherry-tomatoes","olives","parsley","basil","spices","salt","pepper","lemon","olive-oil","parmesan"],
  ingredientLines:[
    {text:"½ package pasta (penne recommended)", qty:0.5, unit:"pack", name:"pasta", prep:"penne recommended"},
    {text:"1 large shallot or ½ red onion", qty:1, unit:"", name:"shallot", prep:"large, or 1/2 red onion"},
    {text:"1 large carrot, small dice", qty:1, unit:"", name:"carrot", prep:"large, small dice"},
    {text:"1 large celery stalk, small dice", qty:1, unit:"", name:"celery", prep:"1 large stalk, small dice"},
    {text:"½ large cauliflower, tiny florets", qty:0.5, unit:"", name:"cauliflower", prep:"large, tiny florets"},
    {text:"1 small green chili, very finely diced", qty:1, unit:"", name:"green chili", prep:"small, very finely diced"},
    {text:"1 medium zucchini, small dice", qty:1, unit:"", name:"zucchini", prep:"medium, small dice"},
    {text:"4 large garlic cloves, finely chopped", qty:4, unit:"clove", name:"garlic", prep:"large, finely chopped"},
    {text:"12 cherry tomatoes, sliced", qty:12, unit:"", name:"cherry tomatoes", prep:"sliced"},
    {text:"6-7 Kalamata olives, roughly chopped", qty:7, unit:"", name:"Kalamata olives", prep:"roughly chopped", qtyText:"6-7"},
    {text:"⅓ cup parsley", qty:0.3333333333333333, unit:"cup", name:"parsley", prep:"roughly chopped"},
    {text:"¼ cup basil", qty:0.25, unit:"cup", name:"basil", prep:"roughly chopped"},
    {text:"1 tablespoon pasta seasoning / Italian herb mix", qty:1, unit:"tbsp", name:"pasta seasoning / Italian herb mix"},
    {text:"coarse salt", qty:null, unit:"", name:"coarse salt"},
    {text:"cracked black pepper", qty:null, unit:"", name:"black pepper", prep:"cracked"},
    {text:"1½ cups pasta water", qty:1.5, unit:"cup", name:"pasta water"},
    {text:"Zest of 1 small lemon", qty:1, unit:"", name:"lemon", prep:"zest, small"},
    {text:"a drizzle of olive oil", qty:null, unit:"", name:"olive oil", prep:"a drizzle, to serve"},
    {text:"lots of Parmesan", qty:null, unit:"", name:"Parmesan", prep:"lots, to serve"}
  ],
  steps:[
    "Cook the pasta to al dente (usually a minute less than the package says). Before draining, reserve a cup and a half of the cooking water.",
    "In a wide pan with a generous amount of olive oil, sauté the shallot. After 2 minutes add the carrot, celery, chili and cauliflower and stir.",
    "After 2-3 minutes add the remaining vegetables and herbs, stir and let everything roast together. Add the seasoning and the pasta water.",
    "When the sauce bubbles, add the pasta and lemon zest. Check for salt.",
    "Serve with a drizzle of olive oil and plenty of Parmesan."
  ],
  tips:"Add any herb you like. The secret is cutting the vegetables small so they cook fast and land in every bite."
},
{
  id:"29579", diet:"Meat", image:"29579.jpg", category:"Chicken",
  name:"Quick Chicken and Rice Noodle Stir-Fry", searchAlias:"מוקפץ עוף ואטריות אורז זריז",
  creator:"Tali Bar", time:"25 min", serves:"Serves 4",
  video:"https://www.facebook.com/reel/1149391067044677",
  intro:"Chicken breast cubes in a maple-soy-cornstarch marinade, stir-fried with onion, carrot, cabbage and rice noodles in a teriyaki, sweet chili, peanut butter and sesame oil sauce.",
  needs:["noodles","chicken","maple","soy","cornflour","onion","carrots","cabbage","chili","peanut-butter","teriyaki","sweet-chili","sesame-oil","salt","pepper","oil"],
  ingredientLines:[
    {text:"¼ bag 5 mm rice noodles", qty:0.25, unit:"pack", name:"rice noodles", prep:"5 mm"},
    {text:"boiling water", qty:null, unit:"", name:"water", prep:"boiling"},
    {group:"For the chicken"},
    {text:"2 plump chicken breasts, medium cubes", qty:2, unit:"", name:"chicken breast", prep:"plump, medium cubes"},
    {text:"1 tablespoon maple syrup", qty:1, unit:"tbsp", name:"maple syrup"},
    {text:"1 tablespoon low-sodium soy sauce", qty:1, unit:"tbsp", name:"soy sauce", prep:"low-sodium"},
    {text:"2 tablespoons cornstarch", qty:2, unit:"tbsp", name:"cornstarch"},
    {group:"For the stir-fry"},
    {text:"1 onion, halved and sliced", qty:1, unit:"", name:"onion", prep:"halved and sliced into strips"},
    {text:"1 carrot, matchsticks", qty:1, unit:"", name:"carrot", prep:"matchsticks"},
    {text:"¼ white cabbage, thinly sliced", qty:0.25, unit:"", name:"white cabbage", prep:"thinly sliced"},
    {text:"½ green chili, diced (optional)", qty:0.5, unit:"", name:"green chili", prep:"diced, optional"},
    {text:"1 teaspoon peanut butter", qty:1, unit:"tsp", name:"peanut butter"},
    {text:"2 tablespoons low-sodium soy sauce", qty:2, unit:"tbsp", name:"soy sauce", prep:"low-sodium"},
    {text:"2 tablespoons teriyaki", qty:2, unit:"tbsp", name:"teriyaki"},
    {text:"1½ tablespoons sweet and sour chili sauce", qty:1.5, unit:"tbsp", name:"sweet and sour chili sauce"},
    {text:"1 tablespoon sesame oil", qty:1, unit:"tbsp", name:"sesame oil"},
    {text:"salt", qty:null, unit:"", name:"salt", prep:"to taste"},
    {text:"pepper", qty:null, unit:"", name:"pepper", prep:"to taste"}
  ],
  steps:[
    "Soak the rice noodles in a bowl of boiling water for 10 minutes.",
    "Mix the chicken cubes with the maple, soy and cornstarch. Chop all the vegetables.",
    "In a hot pan with a little oil, fry the onion. After 2 minutes add the chicken and stir well until sealed on all sides.",
    "Add the peanut butter and stir, then the rest of the vegetables. Let them roast a little.",
    "Drain and rinse the noodles, add to the pan with the remaining seasonings, toss and serve."
  ],
  tips:"The cornstarch in the marinade keeps the chicken juicy and thickens the sauce. Napa cabbage works instead of white."
},
{
  id:"29701", diet:"Vegetarian", image:"29701.jpg", category:"Pasta",
  name:"Spaghetti al Limone with Butter and Garlic", searchAlias:"ספגטי לימון, חמאה ושום",
  creator:"Tom Franz", time:"20 min", serves:"Serves 2-3",
  video:"https://www.facebook.com/reel/1746463432738199",
  intro:"Garlic turned golden in olive oil, butter browned to a nutty hue, lemon zest and pasta water that become a glossy sauce. Plenty of Parmesan on top.",
  needs:["pasta","olive-oil","butter","garlic","lemon","salt","pepper","basil","parmesan","chili"],
  ingredientLines:[
    {text:"250 g spaghetti", qty:250, unit:"g", name:"spaghetti"},
    {text:"3 tablespoons olive oil", qty:3, unit:"tbsp", name:"olive oil"},
    {text:"40 g butter", qty:40, unit:"g", name:"butter"},
    {text:"2-3 garlic cloves, thinly sliced", qty:3, unit:"clove", name:"garlic", prep:"thinly sliced", qtyText:"2-3"},
    {text:"Zest of half a lemon (yellow part only)", qty:0.5, unit:"", name:"lemon", prep:"zest (yellow part only)"},
    {text:"salt", qty:null, unit:"", name:"salt"},
    {text:"cracked black pepper", qty:null, unit:"", name:"black pepper", prep:"cracked"},
    {text:"A ladle of pasta cooking water", qty:1, unit:"", name:"pasta cooking water", prep:"a ladle"},
    {text:"A few basil or sage leaves, chopped", qty:null, unit:"", name:"basil", prep:"or sage, a few leaves, chopped"},
    {text:"Freshly grated Parmesan to serve", qty:null, unit:"", name:"parmesan", prep:"freshly grated, to serve"}
  ],
  steps:[
    "Cook the spaghetti in plenty of salted boiling water until al dente. Reserve some cooking water and drain.",
    "In a wide pan heat the olive oil, add the garlic and fry over medium heat until golden (not brown!).",
    "Add the butter and let it brown lightly to a golden hue for a nutty depth.",
    "Add the lemon zest, stir 20-30 seconds, and add the chopped basil or sage.",
    "Gradually pour in some cooking water while stirring until the sauce thickens slightly, add the pasta and more water if needed. Season with salt and pepper.",
    "Plate and shower generously with Parmesan."
  ],
  tips:"Upgrade: a drop of chili oil or chili flakes for those who like it spicy."
},
{
  id:"29818", diet:"Vegetarian", image:"29818.jpg", category:"Salads",
  name:"Roasted Tomato Salad with Burrata and Bruschetta", searchAlias:"סלט עגבניות צלויות עם בוראטה וברוסקטה",
  creator:"Tom Franz", time:"45 min", serves:"Serves 4-6",
  video:"https://www.facebook.com/reel/1343927357409383",
  intro:"Ripe tomatoes roasted in the oven with whole hot peppers until they split, then dressed with lemon, thyme and red onion. Served on bruschetta with burrata.",
  needs:["tomatoes-fresh","chili","olive-oil","salt","lemon","thyme","red-onion","bread","burrata"],
  ingredientLines:[
    {text:"8-10 ripe tomatoes (Roma / round)", qty:10, unit:"", name:"tomato", prep:"ripe (Roma / round)", qtyText:"8-10"},
    {text:"2-4 hot peppers (red / green)", qty:4, unit:"", name:"hot pepper", prep:"red / green", qtyText:"2-4"},
    {text:"Excellent extra virgin olive oil", qty:null, unit:"", name:"extra virgin olive oil"},
    {text:"Coarse salt", qty:null, unit:"", name:"coarse salt"},
    {text:"Juice of 1 lemon", qty:1, unit:"", name:"lemon", prep:"juice"},
    {text:"A pinch of cayenne or chili flakes", qty:1, unit:"pinch", name:"cayenne pepper", prep:"or chili flakes"},
    {text:"A handful of fresh thyme or oregano leaves", qty:1, unit:"handful", name:"thyme", prep:"or fresh oregano, leaves"},
    {text:"1 small red onion, very finely chopped", qty:1, unit:"", name:"red onion", prep:"small, very finely chopped"},
    {text:"bruschetta (toasted baguette slices)", qty:null, unit:"", name:"baguette", prep:"toasted slices for bruschetta, to serve"},
    {text:"fresh burrata", qty:null, unit:"", name:"burrata", prep:"fresh, to serve"}
  ],
  steps:[
    "Preheat the oven to 180°C. Line a tray with parchment and sprinkle with olive oil and coarse salt.",
    "Quarter the tomatoes and lay them skin side down. Add the hot peppers whole. Roast 25-35 minutes until the tomatoes soften and release their juices.",
    "Transfer the tomatoes to a bowl with their juices. Chop the peppers and return them to the bowl.",
    "Add more olive oil, lemon juice, cayenne, thyme and the finely chopped red onion. Mix gently.",
    "Serve on toasted bruschetta with a piece of burrata, a drizzle of olive oil and even a touch of honey or reduced balsamic."
  ],
  tips:"The roasting juices are the dressing, don't throw them out. Can be made a day ahead, the flavors only improve."
},
{
  id:"29836", diet:"Meat", image:"29836.jpg", category:"Chicken",
  name:"Melt-in-the-Mouth Chicken Thighs in Onion-Tomato Sauce", searchAlias:"פרגיות נמסות ברוטב בצל ועגבניות",
  creator:"Elisheva Rosenblum", time:"1 hr 30 min", serves:"Serves 4-6",
  video:"https://www.facebook.com/reel/720283124370646",
  intro:"Elisheva's \"tomato chicken\": flour-dusted boneless thighs covered in a sauce of fried onion, crushed tomatoes, soy and silan. An hour covered in the oven and another quarter hour uncovered.",
  needs:["chicken","flour","onion","oil","canned-tomatoes","soy","honey-silan","salt"],
  ingredientLines:[
    {text:"4-6 boneless chicken thighs", qty:6, unit:"", name:"boneless chicken thigh", qtyText:"4-6"},
    {text:"½ cup flour", qty:0.5, unit:"cup", name:"flour"},
    {group:"For the sauce"},
    {text:"2 large onions", qty:2, unit:"", name:"onion", prep:"large"},
    {text:"A little oil", qty:null, unit:"", name:"oil", prep:"a little"},
    {text:"1 small can crushed / diced tomatoes", qty:1, unit:"can", name:"tomatoes", prep:"crushed / diced, small can"},
    {text:"3 tablespoons unsweetened soy sauce", qty:3, unit:"tbsp", name:"soy sauce", prep:"unsweetened"},
    {text:"3 tablespoons silan (date syrup)", qty:3, unit:"tbsp", name:"silan (date syrup)"},
    {text:"1 teaspoon salt", qty:1, unit:"tsp", name:"salt"}
  ],
  steps:[
    "Coat the thighs in flour and lay them in a baking dish.",
    "In a large pan fry the onion in oil until golden. Add the tomatoes, soy and silan and cook about 5 minutes.",
    "Pour the sauce over the chicken and cover the dish tightly with foil.",
    "Bake in an oven preheated to 180°C convection for about an hour covered, then another quarter hour uncovered."
  ],
  tips:"Works with any cut of chicken. The flour on the thighs thickens the sauce as it bakes."
},
{
  id:"29915", diet:"Fish", image:"29915.jpg", tb2:"29915-chef.jpg", category:"Pasta",
  name:"Caramelised Onion and Chilli Prawn Pasta", searchAlias:"פסטה שרימפס צ'ילי ובצל מקורמל",
  creator:"Thegoodbite", time:"45 min", serves:"Serves 3-4",
  video:"https://www.facebook.com/reel/774875524955080",
  intro:"Onion slowly caramelised in butter and olive oil, prawns seared in crispy chilli oil with garlic and smoked paprika, and a stock-and-Parmesan cream that coats spaghetti.",
  needs:["onion","olive-oil","butter","chili-crisp","shrimp","garlic","paprika","salt","parsley","stock","cream","parmesan","pasta"],
  ingredientLines:[
    {text:"1 onion, finely sliced", qty:1, unit:"", name:"onion", prep:"thinly sliced"},
    {text:"½ tablespoon olive oil", qty:0.5, unit:"tbsp", name:"olive oil"},
    {text:"½ tablespoon unsalted butter", qty:0.5, unit:"tbsp", name:"unsalted butter"},
    {text:"½ tablespoon crispy chilli oil", qty:0.5, unit:"tbsp", name:"crispy chili oil"},
    {text:"300 g raw king prawns", qty:300, unit:"g", name:"king prawns", prep:"large, raw"},
    {text:"3-4 garlic cloves, finely chopped", qty:4, unit:"clove", name:"garlic", prep:"finely chopped", qtyText:"3-4"},
    {text:"1 teaspoon smoked paprika", qty:1, unit:"tsp", name:"smoked paprika"},
    {text:"A pinch of salt", qty:1, unit:"pinch", name:"salt"},
    {text:"A bunch of fresh parsley, stems and leaves, finely chopped", qty:1, unit:"bunch", name:"parsley", prep:"stems and leaves, finely chopped"},
    {text:"150 ml hot chicken or vegetable stock", qty:150, unit:"ml", name:"chicken stock", prep:"or vegetable, hot"},
    {text:"150 ml single cream", qty:150, unit:"ml", name:"single cream"},
    {text:"20 g grated Parmesan", qty:20, unit:"g", name:"parmesan", prep:"grated"},
    {text:"225 g spaghetti", qty:225, unit:"g", name:"spaghetti"}
  ],
  steps:[
    "Heat the butter and olive oil in a large pan, add the onions and cook on a very low heat for 20-30 minutes, stirring regularly, until caramelised. Remove.",
    "Cook the spaghetti in salted water until al dente and reserve some pasta water.",
    "In the same pan heat the chilli oil, add the prawns, garlic, smoked paprika, the parsley stalks and a small handful of leaves, and a pinch of salt. Cook 5 minutes over medium heat.",
    "Add the stock to deglaze, then the cream and the remaining parsley. Return the caramelised onions and bring to a low simmer. Reduce the heat and stir in the Parmesan.",
    "Add the spaghetti and a ladle of pasta water, toss and serve immediately."
  ],
  tips:"Full recipe from the Thegoodbite website. Crispy chilli oil gives both heat and the crunch of fried garlic."
},
{
  id:"29931", diet:"Meat", image:"29931.jpg", category:"Chicken",
  name:"Chicken Thigh and Chickpea Stew in Coconut Cream", searchAlias:"תבשיל פרגיות וגרגירי חומוס בקרם קוקוס",
  creator:"Itai Dagan", time:"45 min", serves:"Serves 4-6",
  video:"https://www.facebook.com/reel/24543075848708920",
  intro:"Boneless thighs charred first under the oven grill, then simmered with golden onion, chickpeas, garlic, ginger, turmeric and coconut cream. Greens at the end. A stew that travels well to work.",
  needs:["chicken","olive-oil","salt","onion","chickpeas","garlic","ginger","turmeric","chili","coconut-milk","water","chard","rice"],
  ingredientLines:[
    {text:"8 boneless chicken thighs (about 1 kg)", qty:8, unit:"", name:"boneless chicken thigh", prep:"about 1 kg"},
    {text:"olive oil", qty:null, unit:"", name:"olive oil"},
    {text:"coarse salt", qty:null, unit:"", name:"coarse salt"},
    {text:"1 large onion, sliced", qty:1, unit:"", name:"onion", prep:"large, sliced"},
    {text:"1 can cooked chickpeas (or 1½ cups soaked and cooked)", qty:1, unit:"can", name:"chickpeas", prep:"cooked (or 1.5 cups soaked and cooked)"},
    {text:"5 garlic cloves, thinly sliced", qty:5, unit:"clove", name:"garlic", prep:"thinly sliced"},
    {text:"1 teaspoon grated fresh ginger", qty:1, unit:"tsp", name:"ginger", prep:"fresh, grated"},
    {text:"1 heaped teaspoon turmeric", qty:1, unit:"tsp", name:"turmeric", prep:"heaped"},
    {text:"1 teaspoon chili flakes (or less)", qty:1, unit:"tsp", name:"chili flakes", prep:"or less"},
    {text:"1 teaspoon salt", qty:1, unit:"tsp", name:"salt"},
    {text:"1 can coconut cream (400 ml)", qty:1, unit:"can", name:"coconut cream", prep:"400 ml"},
    {text:"the same can of hot water", qty:1, unit:"can", name:"hot water", prep:"same can"},
    {text:"A handful of greens: spinach / kale / chard", qty:1, unit:"handful", name:"leafy greens", prep:"spinach / kale / chard"},
    {text:"white rice", qty:null, unit:"", name:"white rice", prep:"to serve"},
    {text:"chopped mint", qty:null, unit:"", name:"mint", prep:"chopped, to serve"}
  ],
  steps:[
    "Heat the oven grill to its highest setting. Arrange the thighs on a tray, drizzle with olive oil and sprinkle coarse salt. Grill about 10 minutes until nicely browned. Set aside.",
    "In a wide pot heat 3-4 tablespoons olive oil and fry the onion to a deep golden color.",
    "Add the chickpeas with the garlic, ginger, turmeric, chili and salt and fry a few more minutes. Mash some of the chickpeas with a wooden spoon to thicken the sauce.",
    "Add the coconut cream, refill the can with boiling water and add that too. Simmer 5-10 minutes over medium heat.",
    "Return the chicken to the pot, lower the heat and cook 10-15 minutes. Add the greens and cook 2-3 minutes until wilted. Adjust seasoning.",
    "Serve over white rice or rice with almonds and raisins, with chopped mint."
  ],
  tips:"Mashing some of the chickpeas is the trick to a thick sauce without flour."
},
{
  id:"29953", diet:"Meat", image:"29953.jpg", category:"Chicken",
  name:"Chicken Thighs with Leek, Garlic and Grapes", searchAlias:"סיר פרגיות, כרישה, שום וענבים",
  creator:"Chen Koren", time:"1 hr 20 min", serves:"Serves 4-6",
  video:"https://www.facebook.com/reel/1337523134179041",
  intro:"Chen Koren's holiday pot: thighs caramelized in honey, then leeks, a whole head of fresh garlic and bunches of sweet grapes. Half a cup of water, a boil, and an hour in the oven.",
  needs:["chicken","honey-silan","salt","pepper","olive-oil","leek","garlic","grapes","water"],
  ingredientLines:[
    {text:"Boneless chicken thighs, halved", qty:null, unit:"", name:"boneless chicken thigh", prep:"halved"},
    {text:"1 tablespoon honey", qty:1, unit:"tbsp", name:"honey"},
    {text:"salt", qty:null, unit:"", name:"salt"},
    {text:"pepper", qty:null, unit:"", name:"pepper"},
    {text:"olive oil", qty:null, unit:"", name:"olive oil"},
    {text:"2 leeks", qty:2, unit:"", name:"leek"},
    {text:"1 head of fresh garlic", qty:1, unit:"", name:"garlic", prep:"1 whole head, fresh"},
    {text:"2-3 bunches of sweet grapes", qty:3, unit:"bunch", name:"grapes", prep:"sweet bunches", qtyText:"2-3"},
    {text:"½ cup water", qty:0.5, unit:"cup", name:"water"}
  ],
  steps:[
    "Fry the thighs in olive oil, season with salt and pepper and add the honey. Let them caramelize over medium heat.",
    "Add the garlic and leeks (leek in thick slices, garlic halved crosswise), then the grapes.",
    "Add half a cup of water, bring to a boil and transfer to the oven for an hour at 180°C, conventional."
  ],
  tips:"A heavy lidded pot does the work. The grapes burst into a sweet sauce that balances the garlic."
},
{
  id:"30038", diet:"Meat", image:"30038.jpg", category:"Chicken",
  name:"Coconut Lemongrass Chicken", searchAlias:"עוף בקוקוס ולמון גראס",
  creator:"Thegoodbite", time:"30 min", serves:"Serves 2",
  video:"https://www.facebook.com/reel/5163190870573142",
  intro:"Chicken breast pounded and coated in cumin, turmeric and chilli, seared and simmered in a creamy sauce of coconut milk, broth, lemongrass and lime. One pan, 578 calories and 47 g protein.",
  needs:["chicken","salt","pepper","spices","turmeric","chili","oil","onion","garlic","coconut-milk","stock","lemongrass","lime","chili-crisp","rice","bok-choy","cashews","sesame","scallion"],
  ingredientLines:[
    {text:"2 medium chicken breasts", qty:2, unit:"", name:"chicken breast", prep:"medium"},
    {text:"1 teaspoon salt", qty:1, unit:"tsp", name:"salt"},
    {text:"black pepper", qty:null, unit:"", name:"black pepper"},
    {text:"1 teaspoon cumin", qty:1, unit:"tsp", name:"cumin"},
    {text:"1 teaspoon turmeric", qty:1, unit:"tsp", name:"turmeric"},
    {text:"1 teaspoon chilli powder", qty:1, unit:"tsp", name:"chili powder"},
    {text:"1 tablespoon oil", qty:1, unit:"tbsp", name:"oil"},
    {text:"1 shallot, finely chopped", qty:1, unit:"", name:"shallot", prep:"finely chopped"},
    {text:"2-3 garlic cloves, grated", qty:3, unit:"clove", name:"garlic", prep:"grated", qtyText:"2-3"},
    {text:"1 red chilli, deseeded and finely chopped", qty:1, unit:"", name:"red chili", prep:"deseeded, chopped"},
    {text:"200 ml coconut milk", qty:200, unit:"ml", name:"coconut milk"},
    {text:"200-300 ml chicken broth", qty:300, unit:"ml", name:"chicken broth", qtyText:"200-300"},
    {text:"1 heaped teaspoon lemongrass paste", qty:1, unit:"tsp", name:"lemongrass paste", prep:"heaped"},
    {text:"1-2 lemongrass stalks, bashed and halved", qty:2, unit:"", name:"lemongrass stalk", prep:"bashed and halved", qtyText:"1-2"},
    {text:"Juice of ½ lime + zest of 1 lime", qty:1, unit:"", name:"lime", prep:"juice of half and zest of 1 whole"},
    {text:"1 teaspoon chilli oil (optional)", qty:1, unit:"tsp", name:"chili oil", prep:"optional"},
    {text:"cooked white rice", qty:null, unit:"", name:"white rice", prep:"cooked, to serve"},
    {text:"2 pak choi", qty:2, unit:"", name:"pak choi", prep:"to serve"},
    {text:"20 g chopped cashews", qty:20, unit:"g", name:"cashews", prep:"chopped, to serve"},
    {text:"black sesame seeds", qty:null, unit:"", name:"black sesame seeds", prep:"to serve"},
    {text:"2-3 spring onions", qty:3, unit:"", name:"spring onion", prep:"to serve", qtyText:"2-3"}
  ],
  steps:[
    "Cover the chicken breasts with cling film and pound to an even 3 cm thickness. Coat in salt, pepper, cumin, turmeric and chilli powder.",
    "Heat the oil in a lidded pan over medium-high heat and sear the chicken 3-4 minutes per side until coloured. Set aside.",
    "Reduce to medium heat and sauté the shallot, garlic and chilli 2 minutes. Add the coconut milk and broth, lemongrass paste and stalks, lime juice and zest. Simmer 10 minutes.",
    "Return the chicken to the sauce, cover and simmer 10-15 minutes until cooked through. Steam the pak choi separately. Adjust the sauce with more broth and add chilli oil if you like.",
    "Serve rice in bowls with the chicken, pak choi and sauce, and garnish with cashews, black sesame and spring onion."
  ],
  tips:"Full recipe from the Thegoodbite website. Light coconut milk saves calories without losing creaminess."
},
{
  id:"30057", diet:"Fish", image:"30057.jpg", category:"Pasta",
  name:"Tuna Bolognese with Caramelized Onions", searchAlias:"בולונז טונה עם בצל מקורמל",
  creator:"Tom Franz", time:"1 hr", serves:"Serves 5-6",
  video:"https://www.facebook.com/reel/838588915181188",
  intro:"The bolognese Tom Franz improvised as a student when he started keeping kosher: canned tuna instead of meat, onion caramelized in the tuna's oil, crushed tomatoes and spices. A rich, quick, Mediterranean sauce.",
  needs:["tuna","onion","garlic","sugar","paprika","oregano","basil","chili","canned-tomatoes","tomato-paste","salt","pepper","pasta"],
  ingredientLines:[
    {text:"2 cans tuna in oil (don't drain, the oil is used)", qty:2, unit:"can", name:"tuna in oil", prep:"do not drain, the oil is used"},
    {text:"2 large onions, finely chopped", qty:2, unit:"", name:"onion", prep:"large, finely chopped"},
    {text:"2 garlic cloves, thinly sliced", qty:2, unit:"clove", name:"garlic", prep:"thinly sliced"},
    {text:"1 teaspoon sugar", qty:1, unit:"tsp", name:"sugar"},
    {text:"¼ teaspoon smoked paprika", qty:0.25, unit:"tsp", name:"smoked paprika"},
    {text:"¼ teaspoon dried oregano", qty:0.25, unit:"tsp", name:"dried oregano"},
    {text:"¼ teaspoon dried basil", qty:0.25, unit:"tsp", name:"dried basil"},
    {text:"A pinch of chili flakes", qty:1, unit:"pinch", name:"chili flakes"},
    {text:"2 cans crushed tomatoes (400 g each)", qty:2, unit:"can", name:"crushed tomatoes", prep:"400 g each"},
    {text:"1 small can tomato paste (100 g)", qty:1, unit:"can", name:"tomato paste", prep:"small can, 100 g"},
    {text:"1 cup pasta cooking water (as needed)", qty:1, unit:"cup", name:"pasta cooking water", prep:"as needed"},
    {text:"Salt and black pepper", qty:null, unit:"", name:"salt and black pepper"},
    {text:"500 g dried pasta", qty:500, unit:"g", name:"dried pasta"}
  ],
  steps:[
    "Fry the chopped onion in the tuna oil in a wide pot over medium-low heat for about 15 minutes until soft and caramelized. Add the sugar toward the end.",
    "Add the garlic, paprika, oregano, basil, chili, salt, pepper and tomato paste. Fry about a minute until fragrant.",
    "Add the crushed tomatoes and the tuna, breaking it up. Simmer 30-60 minutes over low heat until the sauce reduces. If too thick, add pasta water.",
    "Season with salt and pepper, balance with a little more sugar or heat to taste.",
    "Toss the sauce with hot pasta and serve."
  ],
  tips:"Upgrade with chopped black olives, lemon zest or fresh herbs. If you eat cheese with fish, add Parmesan generously."
},
{
  id:"30179", diet:"Vegetarian", image:"30179.jpg", category:"Pasta",
  name:"Pink Beet Pasta", searchAlias:"פסטה ורודה ברוטב סלק",
  creator:"Orcookeat", time:"1 hr 20 min", serves:"Serves 4",
  video:"https://www.facebook.com/reel/1548899929719387",
  intro:"The most magical pasta there is: roasted beet blended with cream into a smooth pink sauce, over a base of butter, garlic, sage and thyme, with pine nuts and Parmesan. Kids love it.",
  needs:["pasta","beets","cream","sage","butter","olive-oil","garlic","thyme","pine-nuts","parmesan","salt","pepper"],
  ingredientLines:[
    {text:"350 g pasta", qty:350, unit:"g", name:"pasta"},
    {text:"1 small beet", qty:1, unit:"", name:"beet", prep:"small"},
    {text:"250 ml cream", qty:250, unit:"ml", name:"cream"},
    {text:"2 sage leaves", qty:2, unit:"", name:"sage", prep:"leaves"},
    {text:"1 tablespoon butter", qty:1, unit:"tbsp", name:"butter"},
    {text:"1 teaspoon olive oil", qty:1, unit:"tsp", name:"olive oil"},
    {text:"4 garlic cloves, crushed", qty:4, unit:"clove", name:"garlic", prep:"crushed"},
    {text:"Thyme", qty:null, unit:"", name:"thyme"},
    {text:"2 tablespoons pine nuts (optional)", qty:2, unit:"tbsp", name:"pine nuts", prep:"optional"},
    {text:"Grated Parmesan", qty:null, unit:"", name:"parmesan", prep:"grated"},
    {text:"¼ cup pasta water", qty:0.25, unit:"cup", name:"pasta water"},
    {text:"Salt and pepper", qty:null, unit:"", name:"salt and pepper"}
  ],
  steps:[
    "Halve the beet, drizzle with oil, wrap and roast an hour at 200°C. Scoop out the flesh and blend with the cream and salt into a smooth sauce.",
    "In a pan sauté the butter, oil, garlic, sage and thyme until lightly golden. Add the pine nuts.",
    "Add the beet sauce and 3 tablespoons Parmesan.",
    "Cook the pasta, reserve a quarter cup of the water and add it to the pan. Stir until the sauce thickens.",
    "Add the pasta to the pan, toss and serve with more Parmesan on top."
  ],
  tips:"Roast the beet ahead (or use pre-cooked beets) and the dish is ready in 20 minutes."
},
{
  id:"30287", diet:"Fish", image:"30287.jpg", category:"Fish",
  name:"Fish with Leek, Tomatoes and Chard", searchAlias:"דג עם כרישה, עגבניות ומנגולד",
  creator:"Chen Reznik", time:"45 min", serves:"Serves 5",
  video:"https://www.facebook.com/reel/1466391517778182",
  intro:"Sea bass or sea bream fillets cooked over a sauce of leek, Roma tomatoes, chard and white wine, with cubes of butter on top. A sauté pan that goes from stovetop to oven.",
  needs:["tomatoes-fresh","leek","chard","fish-white","garlic","wine-white","olive-oil","salt","parsley","butter","lemon"],
  ingredientLines:[
    {text:"7 Roma tomatoes, quartered", qty:7, unit:"", name:"roma tomato", prep:"quartered"},
    {text:"2 leek stalks (light part), thin rounds", qty:2, unit:"", name:"leek", prep:"light part, thin rounds"},
    {text:"1 bunch chard leaves, roughly chopped", qty:1, unit:"bunch", name:"chard", prep:"leaves, roughly chopped"},
    {text:"5 fillets sea bass / sea bream", qty:5, unit:"", name:"sea bass fillet", prep:"or sea bream"},
    {text:"3 garlic cloves, sliced", qty:3, unit:"clove", name:"garlic", prep:"sliced"},
    {text:"2 cups dry white wine", qty:2, unit:"cup", name:"dry white wine"},
    {text:"2 tablespoons olive oil", qty:2, unit:"tbsp", name:"olive oil"},
    {text:"Coarse salt", qty:null, unit:"", name:"coarse salt"},
    {text:"1 tablespoon dried parsley", qty:1, unit:"tbsp", name:"dried parsley"},
    {text:"About 50 g butter in 3 cubes", qty:50, unit:"g", name:"butter", prep:"about 50 g, in 3 cubes"},
    {text:"Lemon to serve", qty:1, unit:"", name:"lemon", prep:"to serve"}
  ],
  steps:[
    "Preheat the oven to 200°C. Heat an oven-safe sauté pan on the stove with 2 tablespoons olive oil.",
    "Add the leek, tomatoes, garlic and a teaspoon of salt and fry 5-7 minutes, stirring lightly. Don't let it burn, it turns bitter.",
    "Add the chard and fry another 3-5 minutes until it loses volume. Add the wine and dried parsley, stir.",
    "Cover and simmer gently about 10 minutes. Turn off, salt on top, scatter the butter cubes and lay the fillets skin side up, pressing lightly into the sauce.",
    "Bake at 200°C convection for 10 minutes, then switch to top grill for 5 minutes (no more, the fish will dry out).",
    "Sprinkle more parsley, squeeze lemon over and serve."
  ],
  tips:"Don't skip the butter, it's what turns the wine and tomatoes into a sauce."
},
{
  id:"30401", diet:"Meat", image:"30401.jpg", category:"Beef",
  name:"Ben Shai's Mongolian Beef", searchAlias:"בקר מונגולי של בן שי",
  creator:"Ben Shai", time:"35 min", serves:"Serves 2",
  video:"https://www.facebook.com/reel/1815313409026207",
  intro:"Beef strips in a cornstarch, baking soda and soy marinade, seared and glazed in a soy, sugar, rice vinegar and white pepper sauce with garlic, ginger and scallion. Over white rice. Works with chicken or tofu too.",
  needs:["beef","cornflour","baking-powder","soy","rice","oil","garlic","ginger","scallion","chili","sesame","sugar","pepper","vinegar","water","sesame-oil"],
  ingredientLines:[
    {group:"Beef marinade"},
    {text:"300-400 g beef strips", qty:400, unit:"g", name:"beef", prep:"strips", qtyText:"300-400"},
    {text:"1 tablespoon cornstarch", qty:1, unit:"tbsp", name:"cornstarch"},
    {text:"½ teaspoon baking soda", qty:0.5, unit:"tsp", name:"baking soda"},
    {text:"about 3 tablespoons soy sauce", qty:3, unit:"tbsp", name:"soy sauce", prep:"about"},
    {group:"Stir-fry"},
    {text:"White (Persian) rice", qty:null, unit:"", name:"white rice", prep:"Persian"},
    {text:"Oil for frying", qty:null, unit:"", name:"oil", prep:"for frying"},
    {text:"2 garlic cloves, chopped", qty:2, unit:"clove", name:"garlic", prep:"chopped"},
    {text:"an equal amount of chopped ginger", qty:2, unit:"clove", name:"ginger", prep:"chopped, equal amount to the garlic"},
    {text:"2 scallions in segments", qty:2, unit:"", name:"scallion", prep:"in segments"},
    {text:"Hot chili / dried cayenne (optional)", qty:null, unit:"", name:"hot chili or dried cayenne", prep:"optional"},
    {text:"Sesame seeds to serve", qty:null, unit:"", name:"sesame seeds", prep:"to serve"},
    {group:"Sauce"},
    {text:"3 tablespoons soy sauce", qty:3, unit:"tbsp", name:"soy sauce"},
    {text:"1 tablespoon brown sugar", qty:1, unit:"tbsp", name:"brown sugar"},
    {text:"½ teaspoon white pepper", qty:0.5, unit:"tsp", name:"white pepper"},
    {text:"1 tablespoon cornstarch", qty:1, unit:"tbsp", name:"cornstarch"},
    {text:"2 tablespoons rice vinegar", qty:2, unit:"tbsp", name:"rice vinegar"},
    {text:"¼ cup water", qty:0.25, unit:"cup", name:"water"},
    {text:"1 teaspoon sesame oil (add after mixing in the cornstarch)", qty:1, unit:"tsp", name:"sesame oil", prep:"add after mixing in the cornstarch"}
  ],
  steps:[
    "Mix the beef with the marinade ingredients and let it tenderize 15-20 minutes. Start a pot of rice.",
    "Mix all the sauce ingredients in a bowl; add the sesame oil last to avoid cornstarch lumps.",
    "Heat oil in a pan and fry the beef until lightly caramelized. Remove and leave only 1-2 tablespoons of oil in the pan.",
    "Fry the garlic, ginger, the white part of the scallions and chili for a few moments, then add the sauce. Let it bubble and thicken and return the beef. Cook until the sauce coats every strip.",
    "Add the green part of the scallions, toss and serve over rice with sesame seeds."
  ],
  tips:"Swapping to chicken or tofu? Skip the baking soda in the marinade. It has nothing to do with Mongolia, but that's the name."
},
{
  id:"30414", diet:"Fish", image:"30414.jpg", category:"Fish",
  name:"Spicy Fish Pot in 5 Minutes of Work", searchAlias:"סיר דגים חריפים ב-5 דקות עבודה",
  creator:"Sigalit Segev Egozi", time:"30 min", serves:"Serves 6",
  video:"https://www.facebook.com/reel/1302699807879172",
  intro:"The simplest, fastest spicy fish pot: tilapia fillets over coriander, garlic and red pepper, a paprika-tomato paste-oil rub, chickpeas on top and 20 minutes on low heat. With fresh challah it's all you need on Shabbat.",
  needs:["fish-white","coriander","pepper-red","chickpeas","garlic","paprika","salt","pepper","turmeric","chili","tomato-paste","oil","water"],
  ingredientLines:[
    {text:"6-7 tilapia / Nile perch fillets", qty:7, unit:"", name:"tilapia or Nile perch fillet", qtyText:"6-7"},
    {text:"1 bunch coriander", qty:1, unit:"bunch", name:"coriander"},
    {text:"1 red bell pepper, thin strips", qty:1, unit:"", name:"red bell pepper", prep:"thin strips"},
    {text:"½ cup canned chickpeas, rinsed", qty:0.5, unit:"cup", name:"canned chickpeas", prep:"rinsed"},
    {text:"5 garlic cloves, halved (or 1 teaspoon garlic powder)", qty:5, unit:"clove", name:"garlic", prep:"halved, or 1 tsp garlic powder"},
    {text:"2½ tablespoons hot paprika", qty:2.5, unit:"tbsp", name:"hot paprika"},
    {text:"1 teaspoon salt", qty:1, unit:"tsp", name:"salt"},
    {text:"¼ teaspoon pepper", qty:0.25, unit:"tsp", name:"pepper"},
    {text:"½ teaspoon turmeric", qty:0.5, unit:"tsp", name:"turmeric"},
    {text:"1 teaspoon chili flakes", qty:1, unit:"tsp", name:"chili flakes"},
    {text:"½ tube tomato paste", qty:0.5, unit:"", name:"tomato paste", prep:"tube"},
    {text:"⅓ cup canola oil", qty:0.33, unit:"cup", name:"canola oil"},
    {text:"1 cup boiling water", qty:1, unit:"cup", name:"water", prep:"boiling"}
  ],
  steps:[
    "In a wide shallow pot scatter half the coriander, the garlic halves and the pepper strips.",
    "Mix the spices, tomato paste and oil into a smooth paste and spread a little on top of each fillet. Arrange the fish in the pot.",
    "Mix the remaining paste with a cup of boiling water and pour around the edge of the pot. Scatter the rest of the coriander and the chickpeas on top.",
    "Bring to a boil, lower the heat and cook 20 minutes. Dip challah and enjoy."
  ],
  tips:"Assemble the pot ahead, keep it in the fridge and put it on the stove 20 minutes before the meal."
},
{
  id:"30531", diet:"Vegetarian", image:"30531.jpg", category:"Pasta",
  name:"Spaghetti alle Noci (Walnut Pasta)", searchAlias:"ספגטי אלה נוצ'ה (אגוזי מלך)",
  creator:"Tom Franz", time:"25 min", serves:"Serves 2-3",
  video:"https://www.facebook.com/reel/2026576808184839",
  intro:"The walnut pasta Al Capone loved: roughly chopped walnuts toasted in olive oil, garlic and parsley, and pasta water with lots of Parmesan binding it all into a comforting sauce.",
  needs:["pasta","walnuts","garlic","parsley","olive-oil","salt","pepper","parmesan"],
  ingredientLines:[
    {text:"250 g spaghetti", qty:250, unit:"g", name:"spaghetti"},
    {text:"1 cup natural walnuts (100-150 g)", qty:1, unit:"cup", name:"walnuts", prep:"natural, 100-150 g"},
    {text:"2-3 garlic cloves", qty:3, unit:"clove", name:"garlic", qtyText:"2-3"},
    {text:"A large handful of parsley", qty:1, unit:"handful", name:"parsley", prep:"large"},
    {text:"Good olive oil", qty:null, unit:"", name:"olive oil", prep:"good quality"},
    {text:"Salt and pepper", qty:null, unit:"", name:"salt and pepper"},
    {text:"½-¾ cup pasta cooking water", qty:0.75, unit:"cup", name:"pasta cooking water", qtyText:"½-¾"},
    {text:"Lots of grated Parmesan, for the sauce and to serve", qty:null, unit:"", name:"parmesan", prep:"grated, lots, for the sauce and to serve"}
  ],
  steps:[
    "Cook the spaghetti in salted boiling water until al dente.",
    "Coarsely grind the walnuts in a food processor (just chopped, not powder) and remove. In the same processor roughly chop the garlic and parsley.",
    "In a wide pan heat a generous amount of olive oil, add the walnuts and fry, stirring, until deeply toasted and fragrant.",
    "Add the garlic-parsley mix and cook 1-2 minutes until the garlic softens but doesn't brown.",
    "Add pasta water (start with half a cup) and the Parmesan and stir into a thick sauce. Add the pasta and toss well.",
    "Serve immediately with more Parmesan on top."
  ],
  tips:"The walnuts should keep some bite, don't grind them to powder."
},
{
  id:"30542", diet:"Vegetarian", image:"30542.jpg", category:"Pasta",
  name:"Cheese Ravioli in Yogurt and Pea Sauce", searchAlias:"רביולי גבינה ברוטב יוגורט ואפונה",
  creator:"Tom Franz", time:"20 min", serves:"Serves 4",
  video:"https://www.facebook.com/reel/1384092083513306",
  intro:"A sauce Tom Franz developed when Greek yogurt launched in Israel: olive oil with garlic, chili and oregano, yogurt that is only warmed, and cheese ravioli cooked with peas. A fall dinner in 20 minutes.",
  needs:["olive-oil","garlic","chili","oregano","greek-yogurt","salt","pepper","ravioli","peas","mint","feta"],
  ingredientLines:[
    {text:"60 ml olive oil (about ⅓ cup)", qty:60, unit:"ml", name:"olive oil", prep:"about ⅓ cup"},
    {text:"2-3 garlic cloves, crushed", qty:3, unit:"clove", name:"garlic", prep:"crushed", qtyText:"2-3"},
    {text:"½ teaspoon chili flakes", qty:0.5, unit:"tsp", name:"chili flakes"},
    {text:"½ teaspoon dried basil or oregano (or fresh)", qty:0.5, unit:"tsp", name:"basil or oregano", prep:"dried or fresh"},
    {text:"2 cups plain or Greek yogurt", qty:2, unit:"cup", name:"plain or Greek yogurt", prep:"tubs"},
    {text:"Salt and pepper", qty:null, unit:"", name:"salt and pepper"},
    {text:"2 packages fresh cheese ravioli", qty:2, unit:"pack", name:"cheese ravioli", prep:"fresh, chilled"},
    {text:"1½ cups frozen garden peas (out of the freezer half an hour ahead)", qty:1.5, unit:"cup", name:"frozen garden peas", prep:"take out of the freezer half an hour ahead"},
    {text:"mint", qty:null, unit:"", name:"mint", prep:"to serve"},
    {text:"crumbled Bulgarian cheese or feta", qty:null, unit:"", name:"Bulgarian cheese", prep:"or feta, crumbled, to serve"}
  ],
  steps:[
    "Fill a large pot with water and bring to a boil.",
    "In a large pan over low heat warm the olive oil, add the garlic and soften gently without browning. Add the chili and oregano and cook another two minutes. Remove from the heat and cool a little.",
    "After about five minutes add the yogurt, salt and pepper and stir. Only warm, don't boil!",
    "When the water boils add the ravioli and peas. Cook 2-3 minutes, drain and transfer straight into the pan with the sauce.",
    "Toss gently so the sauce coats the ravioli. Serve hot with mint and crumbled feta."
  ],
  tips:"Yogurt splits when boiled, so the pan comes off the heat before it goes in."
},
{
  id:"30661", diet:"Vegetarian", image:"30661.jpg", category:"Soups & Sauces",
  name:"Thick Homemade Corn Soup", searchAlias:"מרק תירס סמיך של בית",
  creator:"Ran Ben Ezra", time:"30 min", serves:"Serves 4-6",
  video:"https://www.facebook.com/reel/1208565837897808",
  intro:"A delicate, thick corn soup from one pot, no powders: red onion, garlic and corn blended with cornstarch, another cup of whole corn, soy, and a beaten egg poured in a thin stream.",
  needs:["olive-oil","red-onion","garlic","corn","water","salt","cornflour","soy","eggs","scallion"],
  ingredientLines:[
    {text:"Olive oil", qty:null, unit:"", name:"olive oil"},
    {text:"1 red onion, chopped", qty:1, unit:"", name:"red onion", prep:"chopped"},
    {text:"1 garlic clove", qty:1, unit:"clove", name:"garlic"},
    {text:"2 cups corn kernels", qty:2, unit:"cup", name:"corn kernels"},
    {text:"1.5 liters water", qty:1.5, unit:"l", name:"water"},
    {text:"1 teaspoon salt", qty:1, unit:"tsp", name:"salt"},
    {text:"3 tablespoons cornstarch", qty:3, unit:"tbsp", name:"cornstarch"},
    {text:"3 tablespoons soy sauce", qty:3, unit:"tbsp", name:"soy sauce"},
    {text:"1 egg (or two)", qty:2, unit:"", name:"egg", prep:"or two", qtyText:"1-2"},
    {text:"Scallion to garnish", qty:null, unit:"", name:"scallion", prep:"to garnish"}
  ],
  steps:[
    "Fry the red onion in olive oil until golden. Add the garlic and one cup of corn and stir a minute.",
    "Add the water and bring to a boil. Add the salt and cornstarch, lower the heat and blend into a smooth soup.",
    "Add the second cup of corn and the soy sauce.",
    "Pour in a beaten egg in a thin stream while stirring. One more short boil and the soup is ready. Garnish with scallion."
  ],
  tips:"The cornstarch gives the body, the egg the golden threads. A soup that disappears before it cools."
},
{
  id:"30831", diet:"Vegetarian", image:"30831.jpg", category:"Vegetables & Sides",
  name:"Classic Thai Fried Rice", searchAlias:"אורז מוקפץ תאילנדי קלאסי",
  creator:"Nofar Zohar", time:"15 min (+ cooked rice)", serves:"Serves 2",
  video:"https://www.facebook.com/reel/1114495470669092",
  intro:"Fried rice like in Thailand: a screaming-hot wok, shallot, garlic and scrambled egg, jasmine rice that gets a smoky char, soy, palm sugar and fish sauce, tomato and coriander. Served with cucumber and lime.",
  needs:["rice","onion","eggs","oil","garlic","scallion","tomatoes-fresh","fish-sauce","pepper","sugar","soy","coriander","lime","cucumbers","chili"],
  ingredientLines:[
    {text:"1.5 cups cooked jasmine rice, al dente", qty:1.5, unit:"cup", name:"jasmine rice", prep:"cooked al dente"},
    {text:"1 small shallot, half-moon slices", qty:1, unit:"", name:"shallot", prep:"small, half-moon slices"},
    {text:"1 large egg", qty:1, unit:"", name:"egg", prep:"large"},
    {text:"4 tablespoons sunflower oil", qty:4, unit:"tbsp", name:"sunflower oil"},
    {text:"2 garlic cloves, smashed and chopped", qty:2, unit:"clove", name:"garlic", prep:"smashed and chopped"},
    {text:"2 scallions in 1 cm segments", qty:2, unit:"", name:"scallion", prep:"stalks, in 1 cm segments"},
    {text:"1 Roma tomato, roughly chopped", qty:1, unit:"", name:"roma tomato", prep:"roughly chopped"},
    {text:"2 tablespoons fish sauce (or vegan)", qty:2, unit:"tbsp", name:"fish sauce", prep:"or vegan"},
    {text:"½ teaspoon ground white pepper", qty:0.5, unit:"tsp", name:"ground white pepper"},
    {text:"1 level teaspoon palm sugar", qty:1, unit:"tsp", name:"palm sugar", prep:"level"},
    {text:"1 tablespoon soy sauce", qty:1, unit:"tbsp", name:"soy sauce"},
    {text:"¼ bunch coriander, roughly chopped", qty:0.25, unit:"bunch", name:"coriander", prep:"roughly chopped"},
    {text:"half a lime", qty:0.5, unit:"", name:"lime", prep:"halved, to serve"},
    {text:"a peeled cucumber in thick diagonal slices", qty:1, unit:"", name:"cucumber", prep:"peeled, in diagonal slices, to serve"},
    {text:"a pinch of chili powder", qty:1, unit:"pinch", name:"chili powder", prep:"to serve"}
  ],
  steps:[
    "In a screaming-hot wok add the oil and shallot, toss half a minute and add the garlic and egg. Stir well into scrambled egg.",
    "Add the scallions and toss until charred. Add the rice and stir, spreading it over the whole surface of the wok for a strong char and smoky flavor.",
    "Add the soy, sugar, fish sauce and white pepper and toss until the sauce coats the rice.",
    "Add the tomato and half the coriander for another minute and turn off.",
    "Pack the rice into a bowl and flip onto a plate. Serve with cucumber, the rest of the coriander, chili and a lime wedge."
  ],
  tips:"Day-old rice (cold and dry) gives the right texture. A truly hot wok is the secret to the char."
},
{
  id:"30996", diet:"Meat", image:"30996.jpg", category:"Beef",
  name:"Dana Reicher's Bolognese", searchAlias:"הבולונז של דנה רייכר",
  creator:"Dana Reicher", time:"3 hrs", serves:"Serves 8",
  video:"https://www.facebook.com/reel/2365906250495009",
  intro:"A legendary bolognese kids love too: carrot and onion seared, then simmered in water without stirring until they caramelize, paprika and BBQ seasoning, a kilo of ground short rib and two hours on low heat.",
  needs:["beef","carrots","onion","olive-oil","spices","paprika","tomato-paste","maple","salt","water","pasta","parmesan"],
  ingredientLines:[
    {text:"1 kg good ground short rib", qty:1, unit:"kg", name:"ground short rib", prep:"good quality"},
    {text:"3 large carrots, finely chopped", qty:3, unit:"", name:"carrot", prep:"large, finely chopped"},
    {text:"2 large onions, finely chopped", qty:2, unit:"", name:"onion", prep:"large, finely chopped"},
    {text:"Olive oil, generously", qty:null, unit:"", name:"olive oil", prep:"generously"},
    {group:"Seasoning"},
    {text:"1 tablespoon dried garlic seasoning", qty:1, unit:"tbsp", name:"dried garlic seasoning"},
    {text:"4 tablespoons sweet paprika", qty:4, unit:"tbsp", name:"sweet paprika"},
    {text:"2 tablespoons BBQ seasoning", qty:2, unit:"tbsp", name:"BBQ seasoning"},
    {text:"1 tube tomato paste (200 g)", qty:1, unit:"", name:"tomato paste", prep:"tube, 200 g"},
    {text:"1 tablespoon maple or another sweetener", qty:1, unit:"tbsp", name:"maple syrup", prep:"or another sweetener"},
    {text:"1 teaspoon MSG (optional), salt to taste", qty:1, unit:"tsp", name:"MSG", prep:"optional, salt to taste"},
    {text:"4 cups water", qty:4, unit:"cup", name:"water"},
    {text:"pasta", qty:null, unit:"", name:"pasta", prep:"to serve"},
    {text:"½ cup pasta water", qty:0.5, unit:"cup", name:"pasta water", prep:"to serve"},
    {text:"lots of Parmesan", qty:null, unit:"", name:"Parmesan", prep:"lots, to serve"}
  ],
  steps:[
    "In a wide sauté pan heat olive oil generously. Sear the onion and carrot with a pinch of salt over high heat until the edges turn golden.",
    "Add water to fully cover the vegetables and cook over medium-high heat until it evaporates completely. Don't stir! Only when the water is gone and the smell turns caramelly, start stirring until the onion and carrot are browned and sweet.",
    "Add the paprika, garlic and BBQ seasoning, mix well, then all the tomato paste and cook a minute or two.",
    "Add the ground beef and break it up well with a wooden spoon. Sear over high heat until fully cooked and browned.",
    "Add salt, MSG and maple, pour in 4 cups water, cover and simmer 2 hours over low-medium heat, checking and stirring occasionally. Remove the lid and keep cooking until the sauce reduces and thickens.",
    "Cook pasta, reserve half a cup of the water and add it to the sauce. Toss the pasta in and serve with lots of Parmesan."
  ],
  tips:"Chop the vegetables in a food processor. The evaporating-water-without-stirring step is the secret to the sweetness."
},
{
  id:"31115", diet:"Vegetarian", image:"31115.jpg", category:"Pasta",
  name:"5-Ingredient Mediterranean Pasta", searchAlias:"פסטה ים-תיכונית ב-5 מרכיבים",
  creator:"Tom Franz", time:"35 min", serves:"Serves 3-4",
  video:"https://www.facebook.com/reel/1205500718107679",
  intro:"Feta, garlic, cherry tomatoes and thyme baked in a dish covered in olive oil until everything softens and the tomatoes burst. Pour over pasta and toss. Amazing pasta with zero work.",
  needs:["feta","garlic","cherry-tomatoes","thyme","olive-oil","pasta"],
  ingredientLines:[
    {text:"150 g feta, cubed", qty:150, unit:"g", name:"feta", prep:"cubed"},
    {text:"8 garlic cloves, peeled", qty:8, unit:"clove", name:"garlic", prep:"peeled"},
    {text:"10-15 whole cherry tomatoes", qty:15, unit:"", name:"cherry tomatoes", prep:"whole", qtyText:"10-15"},
    {text:"A few sprigs fresh thyme or dried thyme (optional)", qty:null, unit:"sprig", name:"thyme", prep:"a few sprigs fresh or dried, optional"},
    {text:"Good olive oil", qty:null, unit:"", name:"olive oil", prep:"good quality"},
    {text:"½ package pasta", qty:0.5, unit:"pack", name:"pasta"}
  ],
  steps:[
    "Put the feta, garlic, cherry tomatoes and thyme in an oven-safe dish. Pour olive oil generously (no need to cover).",
    "Bake in an oven preheated to 180°C for 25-30 minutes, until everything softens and the tomatoes burst.",
    "Meanwhile cook half a package of pasta according to the instructions.",
    "Pour the hot sauce over the pasta, add a spoon of cooking water and toss well. Taste and adjust salt."
  ],
  tips:"The feta melts into the oil and becomes a creamy sauce. No salt needed, the feta is salty enough."
},
{
  id:"31245", diet:"Meat", image:"31245.jpg", category:"Chicken",
  name:"Red Curry Chicken Breast Stew", searchAlias:"תבשיל חזה עוף בקארי אדום",
  creator:"Ayelet Ben-Simon", time:"30 min", serves:"Serves 4",
  video:"https://www.facebook.com/reel/758575963874124",
  intro:"Chicken breast strips with seared red pepper and red onion, garlic, ginger, red curry paste and coconut cream, with lemon, brown sugar, fish sauce and coriander. Over white rice.",
  needs:["chicken","pepper-red","red-onion","garlic","ginger","fish-sauce","oil","sugar","lemon","coriander","curry-red","coconut-milk","rice"],
  ingredientLines:[
    {text:"500 g chicken breast, thin strips", qty:500, unit:"g", name:"chicken breast", prep:"thin strips"},
    {text:"1 red bell pepper, strips", qty:1, unit:"", name:"red bell pepper", prep:"strips"},
    {text:"1 red onion, strips", qty:1, unit:"", name:"red onion", prep:"strips"},
    {text:"2 garlic cloves, crushed", qty:2, unit:"clove", name:"garlic", prep:"crushed"},
    {text:"1 teaspoon grated ginger", qty:1, unit:"tsp", name:"ginger", prep:"grated"},
    {text:"1 tablespoon fish sauce (optional)", qty:1, unit:"tbsp", name:"fish sauce", prep:"optional"},
    {text:"3 tablespoons oil", qty:3, unit:"tbsp", name:"oil"},
    {text:"1 teaspoon dark brown sugar", qty:1, unit:"tsp", name:"dark brown sugar"},
    {text:"Juice of ½ lemon", qty:0.5, unit:"", name:"lemon", prep:"juice"},
    {text:"½ bunch coriander, chopped", qty:0.5, unit:"bunch", name:"coriander", prep:"chopped"},
    {text:"1 tablespoon red curry paste", qty:1, unit:"tbsp", name:"red curry paste"},
    {text:"1 can coconut cream", qty:1, unit:"can", name:"coconut cream"}
  ],
  steps:[
    "In a large hot pan add the oil and immediately the onion and pepper, and sear briefly for flavor and color.",
    "Add the garlic, ginger and chicken strips and stir well until the chicken is almost cooked and turns white.",
    "Add the seasonings, lemon, curry paste and coconut cream and stir.",
    "When bubbling, add the coriander and cook about 15 more minutes. Serve over white rice."
  ],
  tips:"One tablespoon of curry paste gives gentle heat; if you like it hot, add more."
},
{
  id:"31260", diet:"Vegetarian", image:"31260.jpg", category:"Pasta",
  name:"Pasta in Cherry Tomato, Ricotta and Parmesan Sauce", searchAlias:"פסטה ברוטב שרי, ריקוטה ופרמז'ן",
  creator:"Anat Elisha", time:"30 min", serves:"Serves 3-4",
  video:"https://www.facebook.com/reel/826708956449338",
  intro:"Cherry tomatoes softened in the pan with basil and garlic, blended with ricotta and half the Parmesan into a velvety sauce, then back in the pan with chili, pasta and a ladle of cooking water.",
  needs:["pasta","cherry-tomatoes","basil","garlic","olive-oil","salt","pepper","chili","parmesan","ricotta"],
  ingredientLines:[
    {text:"250 g rigatoni or any pasta", qty:250, unit:"g", name:"rigatoni or any other pasta"},
    {text:"3 cups cherry tomatoes", qty:3, unit:"cup", name:"cherry tomatoes"},
    {text:"½ cup packed basil leaves", qty:0.5, unit:"cup", name:"basil", prep:"leaves, packed"},
    {text:"1 garlic clove, finely grated", qty:1, unit:"clove", name:"garlic", prep:"finely grated"},
    {text:"⅓ cup olive oil", qty:0.33, unit:"cup", name:"olive oil"},
    {text:"Salt and pepper", qty:null, unit:"", name:"salt and pepper"},
    {text:"½ teaspoon chili flakes", qty:0.5, unit:"tsp", name:"chili flakes"},
    {text:"100 g grated Parmesan (leave some in cubes if you like)", qty:100, unit:"g", name:"parmesan", prep:"grated, leave some in cubes if you like"},
    {text:"2 heaped tablespoons ricotta", qty:2, unit:"tbsp", name:"ricotta", prep:"heaped"}
  ],
  steps:[
    "Halve the tomatoes. Heat oil in a deep pan and add them with the basil leaves and grated garlic. Season with salt and pepper and fry until the tomatoes are really soft.",
    "Cook the pasta in boiling water with a teaspoon of salt.",
    "Transfer the tomatoes to a food processor with half the Parmesan and the ricotta and blend smooth.",
    "Return the sauce to the pan, add the chili flakes and bring to a boil. Add the pasta with a ladle of cooking water.",
    "Add the rest of the Parmesan and a few more basil leaves, toss well and serve hot."
  ],
  tips:"Cubes of Parmesan that aren't blended give salty surprises in every bite."
},
{
  id:"31317", diet:"Fish", image:"31317.jpg", category:"Fish",
  name:"Salmon in White Wine with Zoodles", searchAlias:"סלמון ביין לבן עם זודלס",
  creator:"Tom Franz", time:"25 min", serves:"Serves 2",
  video:"https://www.facebook.com/reel/25073344482351109",
  intro:"Salmon fillet cooked in a sauce of garlic, chili, lemon, white wine, basil and a spoon of crème fraîche, over zucchini noodles that soak up flavor and stay crunchy. Light and low-carb.",
  needs:["salmon","olive-oil","garlic","chili","lemon","wine-white","basil","cream","zucchini"],
  ingredientLines:[
    {text:"2 skinless salmon fillets", qty:2, unit:"", name:"salmon fillet", prep:"skinless"},
    {text:"3-4 tablespoons olive oil", qty:4, unit:"tbsp", name:"olive oil", qtyText:"3-4"},
    {text:"3 garlic cloves, crushed", qty:3, unit:"clove", name:"garlic", prep:"crushed"},
    {text:"½ teaspoon chili flakes", qty:0.5, unit:"tsp", name:"chili flakes"},
    {text:"Zest and juice of ½ lemon", qty:0.5, unit:"", name:"lemon", prep:"zest and juice"},
    {text:"¾ cup dry white wine", qty:0.75, unit:"cup", name:"dry white wine"},
    {text:"A handful of basil leaves, chopped", qty:1, unit:"handful", name:"basil", prep:"leaves, chopped"},
    {text:"1 heaped tablespoon crème fraîche or cream", qty:1, unit:"tbsp", name:"crème fraîche or sweet cream", prep:"heaped"},
    {text:"1-2 zucchini", qty:2, unit:"", name:"zucchini", qtyText:"1-2"}
  ],
  steps:[
    "Heat olive oil in a wide pan and gently warm the garlic in it. Add the chili flakes.",
    "Add the lemon zest, lemon juice and white wine, bring to a gentle boil and add the basil. Stir in the crème fraîche for a rich sauce.",
    "Lay the salmon in the sauce and baste it. Cover and cook over medium-low heat until the fish is gently cooked through.",
    "Cut the zucchini into thin noodles (knife, julienne peeler or spiralizer) and add to the pan for just 1-2 minutes.",
    "Plate the zoodles as a base with the salmon on top and lots of the sauce."
  ],
  tips:"The zoodles go in only at the end, otherwise they turn watery."
},
{
  id:"31321", diet:"Vegetarian", image:"31321.jpg", tb2:"31321-chef.jpg", category:"Pasta",
  name:"Pasta in Tomato and Peach Cream", searchAlias:"פסטה בקרם עגבניות ואפרסקים",
  creator:"Tom Franz", time:"1 hr", serves:"Serves 4-5",
  video:"https://www.facebook.com/reel/1940888196714396",
  intro:"Italian summer on a plate: caramelized red onion, halved tomatoes and peaches seared and simmered 30 minutes with basil, then blended into a creamy, fruity sauce. Inspired by chef Maor Sabag.",
  needs:["pasta","red-onion","tomatoes-fresh","peach","basil","olive-oil","salt","pepper","ricotta"],
  ingredientLines:[
    {text:"500 g spaghetti", qty:500, unit:"g", name:"spaghetti"},
    {text:"2 red onions, finely chopped", qty:2, unit:"", name:"red onion", prep:"finely chopped"},
    {text:"6-8 ripe tomatoes, halved", qty:8, unit:"", name:"tomato", prep:"ripe, halved", qtyText:"6-8"},
    {text:"3-4 ripe but firm peaches, halved and pitted", qty:4, unit:"", name:"peach", prep:"ripe but firm, halved and pitted", qtyText:"3-4"},
    {text:"A handful of fresh basil leaves", qty:1, unit:"handful", name:"basil", prep:"fresh leaves"},
    {text:"4 tablespoons olive oil", qty:4, unit:"tbsp", name:"olive oil"},
    {text:"Salt and cracked black pepper", qty:null, unit:"", name:"salt and black pepper", prep:"cracked"},
    {text:"ricotta or Parmesan", qty:null, unit:"", name:"ricotta", prep:"or Parmesan, optional"},
    {text:"chopped chives", qty:null, unit:"", name:"chives", prep:"chopped, optional"}
  ],
  steps:[
    "Heat olive oil in a wide pan and caramelize the onion over low heat 10-15 minutes until soft and sweet.",
    "Add the tomato and peach halves cut side down. Sear 3-5 minutes until lightly browned.",
    "Add basil, salt and pepper. Cover and simmer over low heat about 30 minutes. After 10 minutes remove the basil. Take off the heat and cool a little, covered.",
    "Cook the pasta in salted water, drain and reserve some cooking water.",
    "Remove the tomato skins and blend everything smooth and creamy. Return to the pot, warm gently and add cooking water to the desired consistency.",
    "Toss the pasta in the sauce with tongs. Serve hot with a drizzle of olive oil, fresh basil and cheese."
  ],
  tips:"Firm peaches, not too soft, so they keep their flavor and don't turn to water."
},
{
  id:"31720", diet:"Meat", image:"31720.jpg", category:"Chicken",
  name:"Oven Curry-Coconut Chicken Drumsticks", searchAlias:"שוקי עוף בקארי וקוקוס בתנור",
  creator:"Yinon Beeri", time:"1 hr 20 min", serves:"Serves 4",
  video:"https://www.facebook.com/reel/1194628665833403",
  intro:"Five minutes of work: drumsticks with curry powder, olive oil and salt into a blazing oven, then cherry tomatoes and an hour on low heat, and finally coconut cream and convection until the sauce bubbles. With rice or mash.",
  needs:["chicken","olive-oil","curry-powder","salt","pepper","cherry-tomatoes","coconut-milk","scallion","coriander","chili","lemon","rice"],
  ingredientLines:[
    {text:"6 chicken drumsticks or thighs", qty:6, unit:"", name:"chicken drumsticks or thighs"},
    {text:"2 tablespoons olive oil", qty:2, unit:"tbsp", name:"olive oil"},
    {text:"2 heaped tablespoons curry powder", qty:2, unit:"tbsp", name:"curry powder", prep:"heaped"},
    {text:"Salt and pepper", qty:null, unit:"", name:"salt and pepper"},
    {text:"2 handfuls cherry tomatoes", qty:2, unit:"handful", name:"cherry tomatoes"},
    {text:"½-1 can coconut cream", qty:1, unit:"can", name:"coconut cream", qtyText:"½-1"},
    {text:"scallion", qty:null, unit:"", name:"scallion", prep:"to serve, optional"},
    {text:"coriander", qty:null, unit:"", name:"coriander", prep:"to serve, optional"},
    {text:"sliced red chili", qty:null, unit:"", name:"red chili", prep:"sliced, to serve, optional"},
    {text:"lemon wedges", qty:null, unit:"", name:"lemon", prep:"wedges, to serve, optional"}
  ],
  steps:[
    "Heat the oven to 250°C or its highest setting. Put the chicken in a dish, sprinkle curry powder generously, a little olive oil, plenty of salt and cracked pepper. Bake about 10 minutes until the chicken whitens and starts to color.",
    "Add the cherry tomatoes, lower to 175°C and bake about an hour, until the chicken is well browned and there is plenty of tasty liquid in the dish.",
    "Add coconut cream so the chicken is half covered, taste and add salt if needed. Spoon the sauce over.",
    "Return to the oven at the highest heat on convection for 7-10 minutes, until the chicken browns again and the sauce bubbles.",
    "Scatter coriander, scallion and chili and serve with lemon wedges and white rice or mash."
  ],
  tips:"Kosher, lactose-free, no frying and kid-friendly. The sauce in the dish is the whole story."
},
{
  id:"31909", diet:"Vegetarian", image:"31909.jpg", category:"Pasta",
  name:"Aglio e Olio with Pangrattato", searchAlias:"פסטה אליו אוליו עם פאנה גראטאטה",
  creator:"Nofar Zohar", time:"20 min", serves:"Serves 1-2",
  video:"https://www.facebook.com/reel/730204636658338",
  intro:"Aglio e olio like in the movies: olive oil perfumed off the heat with parsley stems and garlic, chili, pasta that finishes cooking in the pan, and toasted seasoned breadcrumbs on top.",
  needs:["pasta","olive-oil","garlic","parsley","chili","breadcrumbs","salt"],
  ingredientLines:[
    {text:"130 g spaghetti", qty:130, unit:"g", name:"spaghetti"},
    {text:"11 tablespoons olive oil", qty:11, unit:"tbsp", name:"olive oil"},
    {text:"6 garlic cloves, very finely chopped", qty:6, unit:"clove", name:"garlic", prep:"very finely chopped"},
    {text:"1 bunch parsley", qty:1, unit:"bunch", name:"parsley"},
    {text:"½ red chili in thin rings", qty:0.5, unit:"", name:"red chili", prep:"thin rings"},
    {text:"2 tablespoons breadcrumbs", qty:2, unit:"tbsp", name:"breadcrumbs"},
    {text:"sea salt", qty:null, unit:"", name:"sea salt"},
    {text:"peperoncino chili powder", qty:null, unit:"", name:"peperoncino chili powder", prep:"to serve"}
  ],
  steps:[
    "Boil a pot with plenty of salted water (salty like the sea!) and cook the pasta for ¾ of the package time.",
    "In a pan heat 8 tablespoons oil. Cut off the bottom third of the parsley bunch and add a handful of stems only to the oil, with 5 garlic cloves. Take off the heat for a minute so the garlic doesn't burn and the oil gets perfumed, return to low heat and add the chili.",
    "Just before the garlic burns, add the pasta to the pan with a ladle of cooking water. Adjust salt if needed.",
    "In a separate pan: 3 tablespoons olive oil, a pinch of salt, chopped parsley and breadcrumbs, toasted until the parsley is dry but still green.",
    "Plate: pasta, pangrattato on top, parsley, and peperoncino chili powder."
  ],
  tips:"The pasta finishes cooking in the sauce, so take it out of the water while still firm."
},
{
  id:"31940", diet:"Vegetarian", image:"31940.jpg", category:"Pasta",
  name:"Chef's 10-Minute Aglio e Olio", searchAlias:"אליו אוליו של שף ב-10 דקות",
  creator:"Broadway Clondalkin", time:"10 min", serves:"Serves 1",
  video:"https://www.facebook.com/reel/2824405977890477",
  intro:"The chefs' go-to snack after a shift: linguine, lots of garlic in olive oil, chili, butter, lemon juice and a bunch of parsley. €1.50 a portion. Add prawns or chicken on the side if you like.",
  needs:["pasta","garlic","olive-oil","chili","lemon","parsley","butter","salt","pepper"],
  ingredientLines:[
    {text:"100 g linguine", qty:100, unit:"g", name:"linguine"},
    {text:"5 garlic cloves", qty:5, unit:"clove", name:"garlic"},
    {text:"80 ml olive oil", qty:80, unit:"ml", name:"olive oil"},
    {text:"A good pinch of chili flakes", qty:1, unit:"pinch", name:"chili flakes", prep:"generous"},
    {text:"Juice of half a lemon", qty:0.5, unit:"", name:"lemon", prep:"juice"},
    {text:"A good bunch of parsley", qty:1, unit:"bunch", name:"parsley", prep:"a good bunch"},
    {text:"2 knobs of butter", qty:2, unit:"", name:"butter", prep:"knobs"},
    {text:"Salt and pepper", qty:null, unit:"", name:"salt and pepper"}
  ],
  steps:[
    "Cook the linguine in salted water until al dente and reserve some cooking water.",
    "In a pan over low heat warm the olive oil with the sliced garlic until gently golden. Add the chili flakes.",
    "Add the pasta to the pan with a little cooking water, the butter and lemon juice and toss into a glossy sauce.",
    "Add chopped parsley, salt and pepper, toss and serve."
  ],
  tips:"Prawns or marinated chicken on the side make it a full meal."
},
{
  id:"32150", diet:"Vegetarian", image:"32150.jpg", category:"Pasta",
  name:"Fresh Fettuccine with Artichoke, Olives and Sun-Dried Tomatoes", searchAlias:"פטוצ'יני טרי עם ארטישוק, זיתים ועגבניות מיובשות",
  creator:"David Guedj", time:"25 min", serves:"Serves 4",
  video:"https://www.facebook.com/reel/1095415285858433",
  intro:"Restaurant-style fresh pasta from a ready-made chilled dough: fold, slice into ribbons, two minutes of cooking, and a high-heat toss with red onion, garlic, artichoke, Kalamata, sun-dried tomatoes, basil and pine nuts.",
  needs:["pasta","salt","water","butter","olive-oil","red-onion","garlic","artichoke","olives","sundried-tomatoes","pepper","basil","pine-nuts","parmesan"],
  ingredientLines:[
    {text:"1 package rolled chilled pasta dough (or 400 g fresh fettuccine)", qty:1, unit:"pack", name:"chilled rolled pasta dough", prep:"or 400 g fresh fettuccine"},
    {text:"a little salt", qty:null, unit:"", name:"salt", prep:"a little"},
    {text:"boiling water", qty:null, unit:"", name:"water", prep:"boiling"},
    {text:"40 g butter", qty:40, unit:"g", name:"butter"},
    {text:"2 tablespoons olive oil", qty:2, unit:"tbsp", name:"olive oil"},
    {text:"Strips from half a large red onion", qty:0.5, unit:"", name:"red onion", prep:"large, in strips"},
    {text:"2 garlic cloves, sliced", qty:2, unit:"clove", name:"garlic", prep:"sliced"},
    {text:"1 jar artichoke quarters (150-200 g)", qty:1, unit:"", name:"artichoke quarters", prep:"jar, 150-200 g"},
    {text:"3 tablespoons pitted Kalamata olives", qty:3, unit:"tbsp", name:"kalamata olives", prep:"pitted"},
    {text:"1 jar sun-dried tomatoes (150 g)", qty:1, unit:"", name:"sun-dried tomatoes", prep:"jar, 150 g"},
    {text:"½ teaspoon coarse salt, ¼ teaspoon black pepper", qty:null, unit:"", name:"coarse salt and black pepper", prep:"½ tsp coarse salt, ¼ tsp black pepper"},
    {text:"A generous handful of fresh basil leaves", qty:1, unit:"handful", name:"basil", prep:"fresh leaves, a generous handful"},
    {text:"2 tablespoons toasted pine nuts", qty:2, unit:"tbsp", name:"pine nuts", prep:"toasted"},
    {text:"Parmesan shavings to serve", qty:null, unit:"", name:"parmesan", prep:"shavings, to serve"}
  ],
  steps:[
    "Lay the pasta dough on the counter and fold both sides toward the middle into a long log. Cut with a sharp knife into 1 cm slices and open them by hand into fettuccine ribbons.",
    "Cook in salted boiling water about two minutes, drain, plunge into ice water to stop the cooking and drain again. Reserve half a ladle of the cooking water.",
    "In a pan put the butter, olive oil and onion strips over maximum heat and fry until golden, stirring, it all happens fast.",
    "Add the artichoke, olives, sun-dried tomatoes, salt and pepper and stir briefly. Add the reserved water and immediately the pasta.",
    "Still over high heat add the basil and pine nuts, toss with tongs for about a minute. Serve with Parmesan shavings."
  ],
  tips:"No ready dough? Works great with dried fettuccine too, just cook per the package."
},
{
  id:"32207", diet:"Vegetarian", image:"32207.jpg", category:"Vegetables & Sides",
  name:"Probiotic Fermented Cucumbers", searchAlias:"מלפפונים כבושים פרוביוטיים",
  creator:"Michal Mosseri", time:"10 min (+ a few days)", serves:"1 jar",
  video:"https://www.facebook.com/reel/1179210641037601",
  intro:"Naturally fermented pickles: small cucumbers in a jar with garlic, peppercorns, hot pepper and dill, covered in brine (a teaspoon of salt per cup). Open once a day to release gas, and after a few days when the color changes, they're ready.",
  needs:["cucumbers","garlic","pepper","chili","dill","water","salt","cabbage"],
  ingredientLines:[
    {text:"Small fresh cucumbers", qty:null, unit:"", name:"cucumber", prep:"small, fresh"},
    {text:"1 garlic clove, cut", qty:1, unit:"clove", name:"garlic", prep:"cut"},
    {text:"Black peppercorns", qty:null, unit:"", name:"black peppercorns"},
    {text:"Hot pepper", qty:null, unit:"", name:"hot pepper"},
    {text:"Fresh dill", qty:null, unit:"", name:"dill", prep:"fresh"},
    {text:"water", qty:null, unit:"", name:"water"},
    {text:"1 teaspoon salt per cup of water", qty:1, unit:"tsp", name:"salt", prep:"per cup of water"},
    {text:"A cabbage leaf to seal", qty:1, unit:"", name:"cabbage leaf", prep:"to seal"}
  ],
  steps:[
    "Wash the cucumbers well and pack them into a glass jar that seals tightly.",
    "Add the garlic, peppercorns, hot pepper and dill.",
    "Cover with water and add a teaspoon of salt per cup of water. Important: all cucumbers fully submerged, otherwise mold develops. Seal with a cabbage leaf that holds them under.",
    "Close the jar and once a day briefly open the lid to release gas.",
    "After a few days (depending on the weather), when the cucumbers change color, they're ready. Move to the fridge."
  ],
  tips:"Summer takes 3-4 days, winter a week. The brine itself is full of probiotics."
},
{
  id:"32783", diet:"Vegetarian", image:"32783.jpg", category:"Pasta",
  name:"3-Ingredient Fettuccine Alfredo", searchAlias:"פטוצ'יני אלפרדו מ-3 מרכיבים",
  creator:"Ben Shai", time:"15 min", serves:"Serves 2",
  video:"https://www.facebook.com/reel/1293589885645303",
  intro:"The original Alfredo, no cream and no tricks: fresh pasta, butter and finely grated Parmesan that come together with a little cooking water into a creamy sauce. Ready-made pasta dough is the perfect shortcut.",
  needs:["pasta","butter","parmesan","salt"],
  ingredientLines:[
    {text:"1 package rolled fresh pasta dough (or 250 g fresh fettuccine)", qty:1, unit:"pack", name:"fresh rolled pasta dough", prep:"or 250 g fresh fettuccine"},
    {text:"100 g butter", qty:100, unit:"g", name:"butter"},
    {text:"100 g Parmesan, very finely grated", qty:100, unit:"g", name:"parmesan", prep:"very finely grated"},
    {text:"Salt for the water", qty:null, unit:"", name:"salt", prep:"for the water"}
  ],
  steps:[
    "Take the pasta dough out of the package, roll and cut into thin ribbons (fettuccine). Have the butter and Parmesan ready beforehand.",
    "Boil a pot of salted water and cook the pasta about a minute and a half, until al dente.",
    "Transfer to a bowl with a little cooking water, add the butter, and while stirring add the Parmesan until a creamy sauce coats the pasta. Add more pasta water gradually as needed."
  ],
  tips:"Another method: mix the butter and Parmesan first, add pasta water gradually into a smooth sauce, then toss with the pasta."
},
{
  id:"32797", diet:"Meat", image:"32797.jpg", category:"Chicken",
  name:"Tom Franz's Mother's Onion Chicken (Zwiebelhähnchen)", searchAlias:"עוף בבצל של אמא של תום פרנץ (צוויבל-הנשן)",
  creator:"Tom Franz", time:"2 hrs 30 min", serves:"Serves 6",
  video:"https://www.facebook.com/reel/1445126320103105",
  intro:"The recipe Tom Franz grew up on, from his late mother Karin: chicken thighs buried in a kilo and a half of sliced onion, brown sugar, salt and pepper. Two hours covered in the oven, then uncovered, for a sweet-salty caramel sauce and chicken that falls off the bone.",
  needs:["chicken","onion","sugar","salt","pepper","oil","rice"],
  ingredientLines:[
    {text:"6 chicken thighs", qty:6, unit:"", name:"chicken thigh"},
    {text:"1.5 kg onions, halved and thinly sliced", qty:1.5, unit:"kg", name:"onion", prep:"halved and thinly sliced"},
    {text:"3 tablespoons brown sugar", qty:3, unit:"tbsp", name:"brown sugar"},
    {text:"Salt and pepper to taste", qty:null, unit:"", name:"salt and pepper", prep:"to taste"},
    {text:"3-4 tablespoons canola or olive oil", qty:4, unit:"tbsp", name:"canola or olive oil", qtyText:"3-4"},
    {text:"To serve: white rice or mashed potatoes", qty:null, unit:"", name:"white rice or mashed potatoes", prep:"to serve"}
  ],
  steps:[
    "Preheat the oven to 180°C. Halve the onions and slice thinly.",
    "Spread a little more than half the onions in a baking dish and drizzle a little oil. Arrange the chicken skin side down, season with salt, pepper and brown sugar. Cover with the remaining onions and a little more oil.",
    "Seal with parchment and foil and bake an hour and a half to two hours, until the chicken is tender and the onions caramelize.",
    "Remove the cover, flip the chicken skin side up, spoon the juices over and return to the oven 25-35 minutes until the skin is golden and the onions deeply caramelized. Taste the juices and balance salt, pepper and sugar.",
    "Serve hot with rice or mash to soak up the sauce."
  ],
  tips:"The longer the chicken and onions stay covered in the oven, the richer the caramel. Add sliced carrot or whole garlic cloves to the bake. Tom's mother served it with spätzle."
},
{
  id:"32911", diet:"Meat", image:"32911.jpg", tb2:"32911-chef.jpg", category:"Beef",
  name:"Chen Koren's Quick Oshpalov", searchAlias:"אושפלאו זריז של חן קורן",
  creator:"Chen Koren", time:"2-3 hrs", serves:"Serves 6",
  video:"https://www.facebook.com/reel/1298519381881817",
  intro:"The quick version of the oshpalov of dreams: cubed short rib seared on onion and cooked an hour in its own juices to a caramel, then carrot matchsticks, dates, rice, coriander and scallion, and 3 cups of water on the lowest heat.",
  needs:["beef","onion","olive-oil","salt","pepper","carrots","dates","rice","coriander","scallion","water"],
  ingredientLines:[
    {text:"300-400 g short rib, small cubes", qty:400, unit:"g", name:"short rib", prep:"small cubes", qtyText:"300-400"},
    {text:"1-2 onions", qty:2, unit:"", name:"onion", qtyText:"1-2"},
    {text:"olive oil", qty:null, unit:"", name:"olive oil"},
    {text:"salt", qty:null, unit:"", name:"salt"},
    {text:"black pepper", qty:null, unit:"", name:"black pepper"},
    {text:"2 carrots, matchsticks", qty:2, unit:"", name:"carrot", prep:"matchsticks"},
    {text:"3 dates, chopped", qty:3, unit:"", name:"dates", prep:"chopped"},
    {text:"2 cups rice", qty:2, unit:"cup", name:"rice"},
    {text:"Chopped coriander and scallion", qty:null, unit:"", name:"coriander and scallion", prep:"chopped"},
    {text:"3 cups water", qty:3, unit:"cup", name:"water"}
  ],
  steps:[
    "Fry the onion in olive oil with pepper and salt. Midway, raise the heat, make room and add the meat. More pepper and salt directly on the meat.",
    "Once seared, lower to the lowest heat and cover for about an hour. Everything releases thick juices that turn into a caramel sauce.",
    "Add the carrot, dates, rice, coriander and scallion and stir.",
    "Add 3 cups water, bring to a boil and lower to the lowest heat. With a good pot and enough olive oil it can go two hours undisturbed. The tahdig on the bottom is a bonus."
  ],
  tips:"The dates are optional but add a lot. A heavy lidded pot makes the difference."
},
{
  id:"33005", diet:"Vegetarian", image:"33005.jpg", category:"Vegetables & Sides",
  name:"Stir-Fried Greens Side", searchAlias:"תוספת ירוקים מוקפצת",
  creator:"Diet Angel", time:"15 min", serves:"Serves 4",
  video:"https://www.facebook.com/reel/745654054768707",
  intro:"The perfect \"free\" side: blanched green beans and broccoli, stir-fried with onion, garlic and zucchini, seasoned with a little sesame oil and soy. Low-carb and goes with any meal.",
  needs:["green-beans","broccoli","zucchini","onion","garlic","sesame-oil","soy"],
  ingredientLines:[
    {text:"Green beans", qty:null, unit:"", name:"green beans"},
    {text:"Broccoli", qty:null, unit:"", name:"broccoli"},
    {text:"Zucchini", qty:null, unit:"", name:"zucchini"},
    {text:"Onion", qty:null, unit:"", name:"onion"},
    {text:"Garlic", qty:null, unit:"", name:"garlic"},
    {text:"A little sesame oil", qty:null, unit:"", name:"sesame oil", prep:"a little"},
    {text:"A little soy sauce", qty:null, unit:"", name:"soy sauce", prep:"a little"}
  ],
  steps:[
    "Blanch the green beans and broccoli a few minutes in boiling water and drain.",
    "Stir-fry in a pan with onion, garlic and zucchini.",
    "Season with a little sesame oil and soy sauce and serve."
  ],
  tips:"Works with any green in the fridge: asparagus, snow peas, Brussels sprouts."
},
{
  id:"33238", diet:"Fish", image:"33238.jpg", category:"Fish",
  name:"Fish en Papillote with Zucchini and Cherry Tomatoes", searchAlias:"דג במעטפה עם זוקיני ושרי",
  creator:"Efrat Lichtenstadt", time:"30 min", serves:"Serves 7",
  video:"https://www.facebook.com/reel/1494811001712058",
  intro:"Tilapia fillet on a bed of zucchini slices and cherry tomatoes, with parsley, coriander, garlic olive oil and lemon slices, sealed in a parchment envelope. The fish steams in its own vapor and comes out soft and juicy. Exactly 13 minutes.",
  needs:["fish-white","lemon","zucchini","cherry-tomatoes","parsley","coriander","olive-oil","salt","pepper","garlic"],
  ingredientLines:[
    {text:"7 skinless tilapia fillets (or another fish), about 150 g each", qty:7, unit:"", name:"tilapia fillet", prep:"or another fish, skinless, about 150 g each"},
    {text:"juice of 1 lemon", qty:1, unit:"", name:"lemon", prep:"juice of 1 lemon"},
    {text:"2 lemons, sliced", qty:2, unit:"", name:"lemon", prep:"sliced"},
    {text:"7 sheets of parchment paper", qty:7, unit:"", name:"parchment paper", prep:"sheets"},
    {text:"2 zucchini in thin slices (mandoline)", qty:2, unit:"", name:"zucchini", prep:"thin slices (mandoline)"},
    {text:"About 25 cherry tomatoes, sliced", qty:25, unit:"", name:"cherry tomatoes", prep:"about 25, sliced"},
    {text:"½ bunch parsley, ½ bunch coriander", qty:null, unit:"", name:"parsley and coriander", prep:"½ bunch each"},
    {text:"⅓ cup olive oil", qty:0.3333333333333333, unit:"cup", name:"olive oil"},
    {text:"2 crushed garlic cloves (garlic optional)", qty:2, unit:"clove", name:"garlic", prep:"crushed, optional"},
    {text:"Salt and pepper", qty:null, unit:"", name:"salt and pepper"}
  ],
  steps:[
    "Rinse the fish, lay on a plate and sprinkle with lemon juice and a little salt. Preheat the oven to 180°C. Mix the olive oil with the crushed garlic in a cup.",
    "In the center of each parchment sheet arrange 2 rows of zucchini slices (the size of the fish) and scatter cherry tomatoes. Lay a few sprigs of parsley and coriander.",
    "Lay the fish on top, pour the garlic oil over generously and season well with salt and pepper. Finish with 2 lemon slices and fold into an envelope.",
    "Put all the envelopes on a tray (in two batches if needed) and bake exactly 13 minutes. Bigger fish: a few more minutes. Serve hot."
  ],
  tips:"Everyone gets a personal envelope, which suits a holiday table. The time is short, don't extend it."
},
{
  id:"29260", diet:"Vegetarian", image:"29260.jpg", category:"Pasta",
  name:"Perfumed Pasta al Limone", searchAlias:"פסטה לימונה מבושמת",
  creator:"Haim Cohen", time:"20 min", serves:"Serves 2",
  video:"https://www.facebook.com/reel/3691997067759744",
  intro:"Haim Cohen's pasta al limone is about the perfume of lemon zest: soft butter mashed with zest, pasta water that makes an emulsion, linguine and Parmigiano. Quantities approximate.",
  needs:["pasta","butter","lemon","salt","parmesan","water"],
  ingredientLines:[
    {text:"250 g linguine", qty:250, unit:"g", name:"linguine"},
    {text:"60-80 g butter at room temperature", qty:80, unit:"g", name:"butter", prep:"room temperature", qtyText:"60-80"},
    {text:"Zest of 2 lemons (yellow part only) + a little juice", qty:2, unit:"", name:"lemon", prep:"zest and a little juice"},
    {text:"Salt (a handful for the water)", qty:1, unit:"handful", name:"salt", prep:"for the water"},
    {text:"Grated Parmigiano, generously", qty:null, unit:"", name:"parmigiano", prep:"grated, generously"},
    {text:"Pasta cooking water", qty:null, unit:"", name:"pasta cooking water"}
  ],
  steps:[
    "Zest the lemons (wash well, and don't reach the bitter white part) and mash the zest into the soft butter. This is the pasta's perfume.",
    "Cook the linguine in boiling water with a handful of salt.",
    "In a wide pan over low heat put the lemon butter with a few spoons of the hot cooking water and stir into an emulsion. The water matters so the butter doesn't burn.",
    "The sauce waits for the pasta, not the other way round: move the pasta straight from the pot to the pan (no draining, the water it brings is good), add Parmigiano and toss.",
    "Serve with more Parmigiano, more zest and a light squeeze of juice."
  ],
  tips:"\"Pasta must not wait, like a date\": have the sauce ready before the pasta is done."
},
{
  id:"30119", diet:"Vegetarian", image:"30119.jpg", category:"Pasta",
  name:"Capri Grandpa's Aglio e Olio", searchAlias:"אליו אוליו של סבא מקאפרי",
  creator:"Cocolarkincooks", time:"20 min", serves:"Serves 4",
  video:"https://www.facebook.com/reel/1486742872816804",
  intro:"Aglio e olio with the twist an old man in Capri taught: lots of chopped garlic and parsley, dried chili, and, against tradition, two tomatoes and half a cup of dry white wine. Linguine that finishes cooking in the sauce. Great for a large group.",
  needs:["pasta","garlic","parsley","olive-oil","chili","tomatoes-fresh","wine-white","salt"],
  ingredientLines:[
    {text:"500 g good linguine", qty:500, unit:"g", name:"linguine", prep:"good quality"},
    {text:"1 head of garlic, chopped", qty:1, unit:"", name:"head of garlic", prep:"chopped"},
    {text:"1 whole bunch parsley, finely chopped", qty:1, unit:"bunch", name:"parsley", prep:"whole, finely chopped"},
    {text:"Lots of olive oil (about ½ cup)", qty:0.5, unit:"cup", name:"olive oil", prep:"a lot"},
    {text:"1 dried chili, chopped", qty:1, unit:"", name:"dried chili", prep:"chopped"},
    {text:"2 tomatoes, chopped", qty:2, unit:"", name:"tomato", prep:"chopped"},
    {text:"½ cup dry white wine", qty:0.5, unit:"cup", name:"dry white wine"},
    {text:"Salt (only for the water, generously)", qty:null, unit:"", name:"salt", prep:"only for the water, generously"}
  ],
  steps:[
    "Chop lots of garlic and all the parsley, finely. Have the wine and tomatoes ready. Everything is prepped because cooking takes minutes.",
    "In a cold pan put lots of olive oil, the garlic and chili, and bring up to medium heat. Cook until just before the garlic takes color.",
    "Add the white wine and tomatoes and cook down about 5 minutes. Take off the heat.",
    "Cook the linguine in heavily salted water (the sauce isn't salted) and take it out very al dente, much more than usual.",
    "Transfer to the pan with a little pasta water and cook, stirring, adding water as needed until the pasta is done. Add all the parsley at the end."
  ],
  tips:"For simple pastas like this, splurge on the more expensive pasta. The parsley goes in only at the end and stays green."
},
{
  id:"30326", diet:"Vegetarian", image:"30326.jpg", category:"Pasta",
  name:"Penne all'Arrabbiata Two Ways", searchAlias:"פנה אראביאטה בשתי דרכים",
  creator:"Vivaldi", time:"20 min", serves:"Serves 1-2",
  video:"https://www.facebook.com/reel/1098493439063330",
  intro:"The Vivaldi restaurant chef makes arrabbiata twice: the home version from whole San Marzano tomatoes crushed and cooked with onion, garlic and fresh chili, and the two-minute restaurant version with ready tomato sauce, garlic, scallion, chili flakes and wine.",
  needs:["pasta","olive-oil","onion","garlic","chili","canned-tomatoes","salt","pepper","scallion","wine-white","parsley"],
  ingredientLines:[
    {group:"Home version"},
    {text:"Olive oil", qty:null, unit:"", name:"olive oil"},
    {text:"¼ onion, rough chop", qty:0.25, unit:"", name:"onion", prep:"roughly chopped"},
    {text:"2-3 garlic cloves, chopped", qty:3, unit:"clove", name:"garlic", prep:"chopped", qtyText:"2-3"},
    {text:"Fresh chili, chopped", qty:null, unit:"", name:"fresh chili", prep:"chopped"},
    {text:"1 small can peeled San Marzano tomatoes", qty:1, unit:"can", name:"San Marzano tomatoes", prep:"small can, peeled"},
    {text:"Salt and pepper", qty:null, unit:"", name:"salt", prep:"and pepper"},
    {group:"Restaurant version"},
    {text:"Olive oil, chopped garlic, scallion", qty:null, unit:"", name:"olive oil", prep:"chopped garlic, scallion"},
    {text:"Chili flakes, salt and pepper", qty:null, unit:"", name:"chili flakes", prep:"salt and pepper"},
    {text:"A splash of white wine", qty:null, unit:"", name:"white wine", prep:"a splash"},
    {text:"Ready tomato sauce", qty:null, unit:"", name:"ready tomato sauce"},
    {group:"For both"},
    {text:"Cooked penne, chopped parsley to finish", qty:null, unit:"", name:"penne", prep:"cooked, chopped parsley to finish"}
  ],
  steps:[
    "Home version: fry the onion, garlic and fresh chili in olive oil until soft, season with salt and pepper. Add the tomatoes and crush them (or crush by hand beforehand). Simmer 5-6 minutes to marry the flavors.",
    "Restaurant version: in an unheated pan put olive oil, garlic, scallion and chili flakes and bring up to heat, just to perfume, not to sear (a blazing pan burns the garlic). Add a splash of wine, then the ready tomato sauce.",
    "For both versions add the cooked penne to the sauce, toss and finish with parsley."
  ],
  tips:"Not much difference between them. Home: whatever's in the pantry. Restaurant: two minutes, wine and scallion."
},
{
  id:"30586", diet:"Vegetarian", image:"30586.jpg", category:"Pasta",
  name:"Fettuccine Alfredo the Italian Way", searchAlias:"פטוצ'יני אלפרדו כמו באיטליה",
  creator:"Vivaldi", time:"10 min", serves:"Serves 1-2",
  video:"https://www.facebook.com/reel/801303449074728",
  intro:"A year after the \"North American\" Alfredo that offended Italy, Vivaldi revisit the Italian version: egg tagliatelle, unsalted butter, two-year-old Parmigiano-Reggiano and pasta water, whipped with residual heat only.",
  needs:["pasta","butter","parmesan","salt","pepper"],
  ingredientLines:[
    {text:"200 g fresh egg tagliatelle / fettuccine", qty:200, unit:"g", name:"egg tagliatelle / fettuccine", prep:"fresh"},
    {text:"50 g unsalted butter", qty:50, unit:"g", name:"unsalted butter"},
    {text:"60-80 g finely grated Parmigiano-Reggiano, maybe more", qty:80, unit:"g", name:"Parmigiano-Reggiano", prep:"finely grated, maybe more", qtyText:"60-80"},
    {text:"Salt for the water", qty:null, unit:"", name:"salt", prep:"for the water"},
    {text:"Cracked black pepper (not orthodox, but recommended)", qty:null, unit:"", name:"black pepper", prep:"cracked (not orthodox, but recommended)"}
  ],
  steps:[
    "Cook the fresh pasta in salted water, it takes only a minute and a half to two.",
    "Meanwhile melt the butter in a pan and turn off the heat.",
    "Drag the pasta into the pan with some water from the pot. Add half the cheese and whip constantly until it becomes a cream. Add a little water if needed.",
    "Add the rest of the cheese and keep whipping with the residual heat until it thickens. Not thick enough? More cheese.",
    "Serve immediately. Cracked black pepper if you like."
  ],
  tips:"The American Alfredo (cream, garlic, egg yolk, protein) and the Italian one are two different dishes. In Italy, this is it."
},
{
  id:"30969", diet:"Meat", image:"30969.jpg", category:"Beef",
  name:"Easy Oven Sofrito", searchAlias:"סופריטו קל בתנור",
  creator:"Chen Koren", time:"3 hrs", serves:"Serves 6",
  video:"https://www.facebook.com/reel/1190143849640375",
  intro:"\"All the work ends at the supermarket\": beef cubes, whole baby potatoes and quartered red onion in an open pot on the stove until everything is charred, then water, parsley, a lid and the oven. Sofrito without all the frying. Quantities approximate.",
  needs:["beef","potato","red-onion","parsley","olive-oil","salt","pepper","water"],
  ingredientLines:[
    {text:"1 kg stewing beef (chuck / roast), large cubes", qty:1, unit:"kg", name:"stewing beef (chuck / roast)", prep:"large cubes"},
    {text:"1 kg baby potatoes, whole with skin", qty:1, unit:"kg", name:"baby potatoes", prep:"whole with skin"},
    {text:"2 red onions, quartered", qty:2, unit:"", name:"red onion", prep:"quartered"},
    {text:"1 bunch parsley (whole, not chopped)", qty:1, unit:"bunch", name:"parsley", prep:"whole, not chopped"},
    {text:"Olive oil, salt, black pepper", qty:null, unit:"", name:"olive oil", prep:"salt, black pepper"},
    {text:"About 1 cup water", qty:1, unit:"cup", name:"water", prep:"about"}
  ],
  steps:[
    "In a wide pot with olive oil put the beef, potatoes and onion. Season with salt and pepper.",
    "Leave over medium-high heat, uncovered, until everything is nicely charred. Stir only occasionally.",
    "Add a cup of water and the whole parsley bunch. Cover.",
    "Transfer to the oven for 2-3 hours at 160-170°C, until the beef melts and the sauce is thick and concentrated."
  ],
  tips:"In the video Chen says \"coriander\" but means parsley. The broth of beef, onion and parsley is the best thing in the world."
},
{
  id:"31986", diet:"Vegetarian", image:"31986.jpg", category:"Vegetables & Sides",
  name:"Persian Drained Rice with Tahdig", searchAlias:"אורז מסונן עם תהדיג",
  creator:"Haim Cohen", time:"1 hr 15 min", serves:"Serves 6",
  video:"https://www.facebook.com/reel/1760868444827952",
  intro:"Persian rice like Haim Cohen's mother made: soaked rice boiled 5 minutes in lots of salted water and drained, a pot with oil and turmeric, an old metal plate to spread the heat, a towel under the lid and 40 minutes on the lowest flame.",
  needs:["rice","water","oil","salt","turmeric","greek-yogurt"],
  ingredientLines:[
    {text:"3 cups basmati rice, soaked at least 20 minutes and rinsed", qty:3, unit:"cup", name:"basmati rice", prep:"soaked at least 20 minutes and rinsed"},
    {text:"About 4 liters water for boiling", qty:4, unit:"l", name:"water", prep:"for boiling"},
    {text:"3 heaped tablespoons salt", qty:3, unit:"tbsp", name:"salt", prep:"heaped"},
    {text:"½ cup oil for the water", qty:0.5, unit:"cup", name:"oil", prep:"for the water"},
    {text:"⅓ cup oil for the pot", qty:0.3333333333333333, unit:"cup", name:"oil", prep:"for the pot"},
    {text:"⅓ cup hot water", qty:0.3333333333333333, unit:"cup", name:"hot water"},
    {text:"a little turmeric", qty:null, unit:"", name:"turmeric", prep:"a little"},
    {text:"To serve: yogurt", qty:null, unit:"", name:"yogurt", prep:"to serve"}
  ],
  steps:[
    "Boil about 4 liters of water with half a cup of oil and 3 tablespoons of salt. Add the soaked rice and cook about 5 minutes until the boil calms and the rice is almost done. Drain.",
    "In a pot (preferably old, not non-stick) put a third cup of hot water, a little turmeric and a third cup of oil. Stir. Place an old metal plate inside if you have one, it spreads the heat and increases the surface.",
    "Drop the drained rice in gently, without mashing or packing. Cover for two minutes.",
    "Lay a clean towel over the pot, close the lid on it and lower to the lowest flame. 40 minutes.",
    "Take the rice out gently from the side without breaking the grains, then lift the crispy tahdig from the bottom. Serve with yogurt."
  ],
  tips:"It's called drained rice because you drain it midway. The smell in the house is a childhood memory passed to the next generation."
},
{
  id:"32663", diet:"Vegetarian", image:"32663.jpg", tb2:"32663-chef.jpg", category:"Pasta",
  name:"Eastern European Jewish Pasta", searchAlias:"פסטה של יהודי מזרח אירופה",
  creator:"Haim Cohen", time:"30 min", serves:"Serves 2",
  video:"https://www.facebook.com/reel/2009556076539991",
  intro:"\"Most Jewish food starts with fried onion\": onion patiently fried in olive oil until brown, an emulsion with pasta water that resembles onion soup, then an egg, two yolks and pecorino off the heat, carbonara style.",
  needs:["pasta","onion","olive-oil","eggs","pecorino","salt","pepper"],
  ingredientLines:[
    {text:"250 g pasta (spaghetti / tagliatelle)", qty:250, unit:"g", name:"pasta (spaghetti / tagliatelle)"},
    {text:"2 large onions, sliced", qty:2, unit:"", name:"onion", prep:"large, sliced"},
    {text:"4 tablespoons olive oil", qty:4, unit:"tbsp", name:"olive oil"},
    {text:"1 whole egg", qty:1, unit:"", name:"egg", prep:"whole"},
    {text:"2 yolks", qty:2, unit:"", name:"egg yolk"},
    {text:"½ cup grated pecorino (or Parmigiano), plus more to serve", qty:0.5, unit:"cup", name:"pecorino", prep:"or Parmigiano, grated, plus more to serve"},
    {text:"A handful of salt for the water", qty:1, unit:"handful", name:"salt", prep:"for the water"},
    {text:"Lots of cracked black pepper", qty:null, unit:"", name:"black pepper", prep:"cracked, a lot"}
  ],
  steps:[
    "Fry the onion in olive oil patiently, over medium-low heat, until truly brown. \"Patience, patience, patience.\"",
    "Meanwhile, carbonara style, whisk in a bowl a whole egg, two yolks, pecorino and black pepper.",
    "Cook the pasta in boiling water with a handful of salt.",
    "Add a ladle of pasta water to the onion: an emulsion of water, olive oil and onion forms, almost an onion soup. Add the pasta and toss.",
    "Off the heat add the egg and cheese mixture and stir quickly into a cream. Don't be afraid. Grate more cheese and serve, fork only."
  ],
  tips:"The eggs go in only off the heat, otherwise you get an omelette."
},
{
  id:"33018", diet:"Vegetarian", image:"33018.jpg", category:"Pasta",
  name:"Marzipan and Rose Pasta", searchAlias:"פסטה מרציפן וורדים",
  creator:"Haim Cohen", time:"25 min", serves:"Serves 2",
  video:"https://www.facebook.com/reel/1335686124841637",
  intro:"\"I may have gone mad, but it's simply wonderful\": white wine reduced to an essence, butter only warmed, dried rose buds, al dente pasta, and grated marzipan and Parmigiano on top. Sweet, salty, bitter.",
  needs:["pasta","wine-white","butter","salt","rose-petals","marzipan","parmesan"],
  ingredientLines:[
    {text:"250 g pasta (tagliatelle / spaghetti)", qty:250, unit:"g", name:"pasta (tagliatelle / spaghetti)"},
    {text:"1 cup white wine", qty:1, unit:"cup", name:"white wine"},
    {text:"50 g butter", qty:50, unit:"g", name:"butter"},
    {text:"Salt", qty:null, unit:"", name:"salt"},
    {text:"4-5 dried rose buds (edible), petals crumbled", qty:5, unit:"", name:"dried rose buds (edible)", prep:"petals crumbled", qtyText:"4-5"},
    {text:"50-80 g marzipan (a lot, if you're doing it)", qty:80, unit:"g", name:"marzipan", prep:"a lot, if you are doing it", qtyText:"50-80"},
    {text:"Grated Parmigiano", qty:null, unit:"", name:"parmigiano", prep:"grated"}
  ],
  steps:[
    "Boil water and salt it. In a pan reduce the white wine until only an essence of wine remains, all the acidity and flavor.",
    "Lower the heat and add the butter. Don't boil, just warm. A pinch of salt.",
    "Crumble in the petals of 4-5 rose buds. A wonderful smell.",
    "Cook the pasta al dente and transfer to the sauce, toss.",
    "Plate. Grate marzipan generously on top (mind your fingers), then Parmigiano. Rose petals around for decoration."
  ],
  tips:"Sweet, salty, marzipan-y. Haim Cohen's mother loved roses; this is a dish full of love."
},
{
  id:"33643", diet:"Meat", image:"33643.jpg", category:"Chicken",
  name:"Chicken with Caramelized Apples", searchAlias:"עוף עם תפוחים מקורמלים",
  creator:"Chen Koren", time:"1 hr 30 min", serves:"Serves 4-6",
  video:"https://www.facebook.com/reel/1763394510959529",
  intro:"Quartered apples caramelized in butter with maple, cinnamon and a slice of ginger, then a cut-up whole chicken seared with onion in a sauté pan and the apples returned to it under a lid. \"Tastier than the chicken\", the most Rosh Hashanah dish there is.",
  needs:["apple","butter","maple","spices","ginger","olive-oil","onion","salt","pepper","chicken"],
  ingredientLines:[
    {text:"5 apples (Chen used 3 and says: at least five), quartered", qty:5, unit:"", name:"apple", prep:"quartered"},
    {text:"1 tablespoon butter", qty:1, unit:"tbsp", name:"butter"},
    {text:"2-3 tablespoons maple syrup (or honey)", qty:3, unit:"tbsp", name:"maple syrup (or honey)", qtyText:"2-3"},
    {text:"A little cinnamon", qty:null, unit:"", name:"cinnamon", prep:"a little"},
    {text:"1 slice fresh ginger", qty:1, unit:"slice", name:"fresh ginger"},
    {text:"Olive oil", qty:null, unit:"", name:"olive oil"},
    {text:"2 onions, sliced", qty:2, unit:"", name:"onion", prep:"sliced"},
    {text:"Salt, black pepper", qty:null, unit:"", name:"salt", prep:"black pepper"},
    {text:"1 whole chicken cut up: 2 thighs, 2 drumsticks, 2 wings (+ breast if you like)", qty:1, unit:"", name:"whole chicken", prep:"cut up: 2 thighs, 2 drumsticks, 2 wings (+ breast if you like)"}
  ],
  steps:[
    "In a pan melt the butter with the maple, cinnamon and ginger slice. Add the apple quarters and caramelize until golden and the sauce thickens. Set aside.",
    "In a sauté pan heat olive oil, add the onion and salt it now, so the onion releases all its flavor and juices into the stew.",
    "Add the chicken pieces and sear them together with the onion.",
    "Return the caramelized apples onto the chicken, more black pepper over everything, cover and cook over low heat about an hour, until the chicken melts off the fork. No water and no powders, all the flavor from the ingredients."
  ],
  tips:"The ginger gives a gentle kick, the maple and apples caramelize like Parisian caramelized apples. It smells like a holiday."
},
{
  id:"29468", diet:"Vegetarian", image:"29468.jpg", category:"Vegetables & Sides",
  name:"Greek-Style Lemon Potatoes", searchAlias:"תפוחי אדמה לימוניים בסגנון יווני",
  creator:"Matt Mancuso", time:"50 min", serves:"Serves 4-6",
  video:"https://www.facebook.com/reel/2102725633815941",
  intro:"The dish a New York private chef makes for the family at least once a week: potato batons roasted in lots of stock, olive oil, lemon juice, garlic and fresh oregano until they soak up all the liquid and turn glassy, buttery and crispy at the edges.",
  needs:["potato","stock","olive-oil","lemon","garlic","oregano","salt"],
  ingredientLines:[
    {text:"1.5 kg potatoes, peeled and cut into thick batons", qty:1.5, unit:"kg", name:"potato", prep:"peeled and cut into thick batons"},
    {text:"2 cups chicken or vegetable stock", qty:2, unit:"cup", name:"chicken or vegetable stock"},
    {text:"½ cup olive oil", qty:0.5, unit:"cup", name:"olive oil"},
    {text:"juice of 2 lemons, plus more to serve", qty:2, unit:"", name:"lemon", prep:"juice, plus more to serve"},
    {text:"8 garlic cloves, crushed", qty:8, unit:"clove", name:"garlic", prep:"crushed"},
    {text:"A handful of fresh oregano", qty:1, unit:"handful", name:"fresh oregano"},
    {text:"Salt", qty:null, unit:"", name:"salt"}
  ],
  steps:[
    "Whisk together the stock, olive oil, lemon juice, garlic, oregano and salt.",
    "Layer the potato batons in a baking dish and pour the liquid over.",
    "Roast at 200°C about 20 minutes, flip the potatoes and roast another 20-25 minutes, until the liquid is absorbed and the potatoes are glassy and crispy at the edges.",
    "Pour the oil left in the dish over the top with more fresh lemon and serve."
  ],
  tips:"Not fully traditional, \"so don't come at me\". The secret is lots of liquid: the potatoes braise in it and then roast."
},
{
  id:"31178", diet:"Meat", image:"31178.jpg", category:"Chicken",
  name:"4 Chicken Marinades for the Whole Week", searchAlias:"4 מרינדות לעוף לכל השבוע",
  creator:"Or Kahal", time:"15 min (+ marinating)", serves:"500 g chicken per marinade",
  video:"https://www.instagram.com/reel/DM2tKSJImP8/",
  intro:"Dietitian Or Kahal upgrades boring chicken: four marinades (Greek yogurt, chimichurri, coriander-lemon, soy-ginger) mixed in zip bags, each cut of chicken in its own bag, flattened, and whatever isn't cooked within two or three days goes to the freezer. Saves the what-to-cook dilemma.",
  needs:["chicken","greek-yogurt","parsley","garlic","olive-oil","lemon","salt","pepper","coriander","red-onion","honey-silan","chili","soy","teriyaki","sriracha","sesame-oil","ginger"],
  ingredientLines:[
    {text:"500 g chicken per marinade: breast fillets or boneless thighs (the difference: about 30 calories per 100 g)", qty:500, unit:"g", name:"chicken breast fillet or boneless thigh", prep:"per marinade"},
    {group:"1. Greek yogurt marinade"},
    {text:"1 cup Greek yogurt (or any plain yogurt)", qty:1, unit:"", name:"Greek yogurt (or plain yogurt)", prep:"1 cup"},
    {text:"A handful of chopped parsley, 2 garlic cloves, 2 tablespoons olive oil, juice of ½ lemon, salt and pepper", qty:1, unit:"handful", name:"parsley", prep:"chopped; also 2 garlic cloves, 2 tbsp olive oil, juice of ½ lemon, salt and pepper"},
    {group:"2. Chimichurri marinade"},
    {text:"A handful each of chopped parsley and coriander, ½ red onion finely chopped, 2 garlic cloves", qty:1, unit:"handful", name:"parsley", prep:"chopped; also a handful of coriander, ½ red onion finely chopped, 2 garlic cloves"},
    {text:"1 tablespoon honey, ¼ cup olive oil, juice of ½ lemon, red chili, salt and pepper", qty:1, unit:"tbsp", name:"honey", prep:"also ¼ cup olive oil, juice of ½ lemon, red chili, salt and pepper"},
    {group:"3. Coriander and lemon marinade"},
    {text:"A handful of chopped coriander, juice of 1 lemon, 2 garlic cloves, ¼ cup olive oil, salt and pepper", qty:1, unit:"handful", name:"coriander", prep:"chopped; also juice of 1 lemon, 2 garlic cloves, ¼ cup olive oil, salt and pepper"},
    {group:"4. Soy and ginger marinade"},
    {text:"3 tablespoons soy sauce, 3 tablespoons teriyaki, 2 tablespoons sriracha, 2 drops sesame oil", qty:3, unit:"tbsp", name:"soy sauce", prep:"also 3 tbsp teriyaki, 2 tbsp sriracha, 2 drops sesame oil"},
    {text:"2 tablespoons honey, 2 tablespoons olive oil, juice of 1 lemon, 1 tablespoon grated ginger, 2 garlic cloves, salt and pepper", qty:2, unit:"tbsp", name:"honey", prep:"also 2 tbsp olive oil, juice of 1 lemon, 1 tbsp grated ginger, 2 garlic cloves, salt and pepper"}
  ],
  steps:[
    "Mix each marinade's ingredients directly in a zip bag.",
    "Add 500 g chicken (breast or thighs) to each bag, seal and massage so the marinade coats every piece.",
    "Flatten the bags. What you'll cook in the next two or three days stays in the fridge, the rest goes flat into the freezer (so it thaws fast).",
    "To cook: thaw, then grill in a hot pan or roast in the oven (200°C, about 20 minutes for thighs / 15 for breast) until cooked and golden."
  ],
  tips:"Per 100 g: chicken breast 160 kcal / 31 g protein / 3.5 g fat; thighs 190 kcal / 29 g protein / 7.5 g fat. Also saves dirty dishes."
},
{
  id:"29802", diet:"Meat", image:"29802.jpg", category:"Chicken",
  name:"Edri's Chicken, Cauliflower and Carrot Pot", searchAlias:"סיר עוף, כרובית וגזר של אדרי",
  creator:"shlakot47 · edrikobi", time:"2 hrs", serves:"Serves 4-5",
  video:"https://www.instagram.com/reel/DQRrl0sCHD0/",
  intro:"\"He's literally begging, so let's try it\": a chicken pot after @edrikobi's recipe, tested and rated 9 out of 10. Onion, halved chicken legs, cauliflower and carrot roughly chopped, turmeric, pepper, tomato paste and a spoon of sugar, water up to the chicken line, 20 minutes on high and an hour and a half on low. Quantities per the video.",
  needs:["olive-oil","onion","chicken","cauliflower","carrots","turmeric","pepper","salt","tomato-paste","sugar","water"],
  ingredientLines:[
    {text:"Olive oil, generously", qty:null, unit:"", name:"olive oil", prep:"generously"},
    {text:"2 onions, roughly chopped", qty:2, unit:"", name:"onion", prep:"roughly chopped"},
    {text:"5 chicken legs, halved (drumstick + thigh)", qty:5, unit:"", name:"chicken leg", prep:"halved (drumstick + thigh)"},
    {text:"1 nice cauliflower, in florets", qty:1, unit:"", name:"cauliflower", prep:"in florets"},
    {text:"4 carrots, in chunks", qty:4, unit:"", name:"carrot", prep:"in chunks"},
    {text:"1 teaspoon turmeric", qty:1, unit:"tsp", name:"turmeric"},
    {text:"1 teaspoon black pepper, salt", qty:1, unit:"tsp", name:"black pepper", prep:"and salt"},
    {text:"2 tablespoons tomato paste", qty:2, unit:"tbsp", name:"tomato paste"},
    {text:"1 tablespoon sugar (don't ask why)", qty:1, unit:"tbsp", name:"sugar"},
    {text:"Water up to the chicken line", qty:null, unit:"", name:"water", prep:"up to the chicken line"}
  ],
  steps:[
    "In a wide pot heat olive oil generously and add the roughly chopped onion.",
    "Add the halved chicken legs, then the cauliflower and carrots on top. No need for precise cutting.",
    "Season with turmeric, black pepper and salt. Add 2 tablespoons tomato paste and a tablespoon of sugar.",
    "Add water up to the chicken line and give the pot a light shake.",
    "Cover and cook 20 minutes on high heat, then lower and cook another hour and a half, until the chicken melts and the sauce is red and thick."
  ],
  tips:"The sugar balances the acidity of the tomato paste. Score: 9 out of 10."
}
);
