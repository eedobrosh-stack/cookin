/* Cookin — batch 4 (2026-08-30): 6 dishes synced from the WhatsApp group */

Object.assign(INGREDIENTS, {
  "oyster-sauce": {label:"Oyster sauce", group:"Asian Pantry", subs:["hoisin","soy"]},
  celery:         {label:"Celery", group:"Vegetables & Fruit", subs:["fennel"]},
  walnuts:        {label:"Walnuts", group:"Pantry & Canned", subs:["pecans","cashews"]},
  pecans:         {label:"Pecans", group:"Pantry & Canned", subs:["walnuts"]},
  "cranberries-dried": {label:"Dried cranberries", group:"Pantry & Canned", subs:[]},
  apple:          {label:"Green apple", group:"Vegetables & Fruit", subs:["pear"]},
  "green-beans":  {label:"Green beans", group:"Vegetables & Fruit", subs:["snow-peas"]},
  "bamboo-shoots":{label:"Bamboo shoots (canned)", group:"Asian Pantry", subs:[]},
  turmeric:       {label:"Turmeric", group:"Pantry & Canned", subs:[]},
  peas:           {label:"Peas", group:"Vegetables & Fruit", subs:["green-beans"]},
  kohlrabi:       {label:"Kohlrabi", group:"Vegetables & Fruit", subs:["cucumbers"]},
  "pomegranate-molasses": {label:"Pomegranate molasses", group:"Pantry & Canned", subs:["honey-silan"]}
});

RECIPES.push(
{
  id:"70885", diet:"Meat", image:"70885.jpg", category:"Chicken",
  name:"Chinese-Style Steamed Shredded Chicken in Soy Sauce",
  searchAlias:"עוף מאודה מגורר ברוטב סויה (בסגנון סיני)",
  creator:"chinesefood0805", time:"45 min", serves:"Serves 3-4",
  video:"https://www.facebook.com/reel/1498359258449522",
  intro:"A whole chicken steamed over an upside-down bowl in a pot, hand-shredded and dressed in a glossy soy-sesame sauce. Recreated from the video.",
  needs:["chicken","ginger","scallion","soy","sesame-oil","sugar","vinegar","garlic"],
  ingredientLines:[
    {text:"1 small whole chicken, or 4-6 thighs / bone-in chicken breast"},
    {text:"3-4 slices fresh ginger"},
    {text:"2-3 scallions (white parts for steaming, greens for garnish)"},
    {text:"Sauce: 4 tbsp soy sauce"},
    {text:"1 tbsp sesame oil"},
    {text:"1 tsp sugar"},
    {text:"1 tsp rice vinegar"},
    {text:"2 garlic cloves, minced"},
    {text:"Toasted sesame seeds and scallion greens, for garnish"}
  ],
  steps:[
    "Place an upside-down bowl in the center of a wide pot — it lifts the chicken above the liquid that collects during steaming.",
    "Set the chicken on the bowl with the ginger and the white parts of the scallions, cover, and steam over medium heat for about 20-25 minutes (check that the thickest part reaches 74°C — a larger chicken needs more time).",
    "Let cool slightly, then hand-shred the chicken into strips, skin included.",
    "Mix the sauce ingredients (feel free to add 2-3 tablespoons of the steaming liquid collected in the pot — it's concentrated chicken broth).",
    "Arrange the shredded chicken on a plate, pour the sauce over, and sprinkle with sesame seeds and scallion greens."
  ],
  tips:"From the comments: the upside-down bowl is there to lift the chicken above the liquid; and make sure to steam long enough — many commenters suspected the chicken in the video wasn't fully cooked."
},
{
  id:"70886", diet:"Meat", image:"70886.jpg", category:"Chicken",
  name:"Thai Basil Chicken (Pad Krapow)",
  searchAlias:"עוף תאילנדי בבזיליקום (פאד קרפאו)",
  creator:"Chris Lee", time:"25 min", serves:"Serves 2",
  video:"https://www.facebook.com/reel/1464300645451653",
  intro:"Cubed boneless chicken thighs in a spicy soy-oyster-sriracha sauce with loads of Thai basil, served over rice with a fried egg. 541 calories per serving.",
  needs:["chicken","soy","oyster-sauce","sriracha","fish-sauce","sugar","garlic","chili","basil","rice","eggs"],
  ingredientLines:[
    {text:"400 g boneless chicken thighs, cubed"},
    {text:"2 tbsp soy sauce"},
    {text:"2 tbsp oyster sauce"},
    {text:"2 tbsp sriracha"},
    {text:"1 tbsp fish sauce"},
    {text:"1 tbsp sugar or sweetener"},
    {text:"1 tbsp minced garlic, plus a bit more for the pan"},
    {text:"1-3 Thai chilies, sliced (to your heat tolerance)"},
    {text:"1 cup Thai basil leaves"},
    {text:"To serve: white rice + a fried egg"}
  ],
  steps:[
    "In a bowl, mix the soy sauce, oyster sauce, sriracha, fish sauce, sugar, and minced garlic.",
    "Over medium-high heat, fry the garlic and sliced chili until lightly golden.",
    "Add the cubed chicken and sear until it develops a golden crust.",
    "Pour in the sauce and stir to coat evenly.",
    "Add the basil and a splash of water and cook until nearly all the liquid has evaporated.",
    "Serve over white rice, topped with a fried egg."
  ],
  tips:"From the comments: for a more authentic version — holy basil (krapow) and a sauce of 1 tsp oyster sauce, 1 tsp light soy sauce, 1/2 tsp dark soy sauce, 1/2 tsp fish sauce, and 1/4 tsp sugar."
},
{
  id:"70890", diet:"Vegetarian", image:"70890.jpg", category:"Salads",
  name:"Green Herb Salad with Cranberries and Nuts",
  searchAlias:"סלט ירוק עם חמוציות ואגוזים",
  creator:"רובי מיכאל", time:"20 min", serves:"Serves 4-6",
  video:"https://www.facebook.com/watch/?v=2325360474600667",
  intro:"A salad of finely chopped greens — celery leaves, mint, cilantro, and parsley — with nuts, cranberries, green apple, and a silan-lemon dressing.",
  needs:["celery","mint","coriander","parsley","walnuts","pecans","cranberries-dried","apple","honey-silan","olive-oil","lemon","salt","pepper"],
  ingredientLines:[
    {text:"Leaves from a whole head of celery (leaves only)"},
    {text:"1 bunch mint — leaves only"},
    {text:"1 bunch cilantro (lower stems removed)"},
    {text:"1 bunch parsley (lower stems removed)"},
    {text:"1/2 cup walnuts (50 g)"},
    {text:"1/2 cup pecans (50 g)"},
    {text:"1/2 cup sweetened dried cranberries (75 g)"},
    {text:"1 fresh green apple"},
    {text:"Dressing: 3 tbsp silan (date syrup, 60 g)"},
    {text:"2 tbsp olive oil"},
    {text:"Juice of a whole lemon"},
    {text:"1 level tsp salt + 1/2 tsp black pepper"}
  ],
  steps:[
    "Finely chop all the greens and transfer to a large bowl that's easy to toss in.",
    "Roughly chop the nuts and add them over the greens along with the cranberries.",
    "In a small bowl, mix the dressing ingredients.",
    "Dice the apple and add it to the bowl.",
    "Stir the dressing again, pour it over, toss well, and transfer to a serving plate."
  ],
  tips:"448K views and 4.8K likes. Stir the dressing again right before pouring — the silan settles at the bottom."
},
{
  id:"70994", diet:"Meat", image:"70994.jpg", category:"Chicken",
  name:"Thai Red Curry with Chicken",
  searchAlias:"קארי אדום תאילנדי עם עוף",
  creator:"Maxi's Kitchen", time:"25 min", serves:"Serves 3-4",
  video:"https://www.facebook.com/reel/2241373829953655",
  intro:"A classic red curry: coconut milk reduced with curry paste, thinly sliced chicken breast, green beans, bamboo shoots, and basil.",
  needs:["coconut-milk","curry-red","stock","sugar","fish-sauce","bamboo-shoots","green-beans","chicken","pepper-red","lime","basil","rice"],
  ingredientLines:[
    {text:"1 can (400 ml) full-fat coconut milk"},
    {text:"2 tbsp red curry paste (Mae Ploy recommended) — or more"},
    {text:"1 cup chicken stock"},
    {text:"1 tbsp sugar"},
    {text:"1 tbsp fish sauce"},
    {text:"1 can bamboo shoots, drained (about 115 g)"},
    {text:"1.5 cups green beans (140 g), cut into 2-3 cm pieces"},
    {text:"450 g chicken breast, very thinly sliced"},
    {text:"1 red bell pepper, cut into thin strips"},
    {text:"Juice of half a lime"},
    {text:"1 cup Thai basil leaves (or regular basil)"},
    {text:"Jasmine rice, for serving"}
  ],
  steps:[
    "Reduce about a third of the coconut milk in a pot over medium heat for 3-5 minutes until it thickens.",
    "Add the curry paste and fry for 1-2 minutes, stirring, until fragrant.",
    "Add the rest of the coconut milk, the stock, sugar, and fish sauce; whisk and bring to a gentle simmer. Taste — if adding more curry paste, it's best to fry it first in a little oil in a small pan.",
    "Add the bamboo shoots and green beans and cook for a minute; add the chicken and cook for 3-5 minutes until done.",
    "Stir in the bell pepper, turn off the heat, and add the lime juice and basil. Serve over jasmine rice."
  ],
  tips:"Tip from the recipe: freeze the chicken breast for 30-40 minutes before slicing — it comes out extra thin. From the comments: kaffir lime leaves are the secret."
},
{
  id:"70995", diet:"Meat", image:"70995.jpg", category:"Soups & Sauces",
  name:"Creamy Vegetable Soup with Chicken and Cornstarch",
  searchAlias:"מרק ירקות קרמי עם עוף וקורנפלור",
  creator:"einfach.hassan", time:"50 min", serves:"Serves 4-6",
  video:"https://www.facebook.com/reel/2182529886022931",
  intro:"A wintry German soup: cornstarch toasted in butter, vegetables simmered and blended into a cream, and a whole chicken breast poached right in the soup and shredded back in.",
  needs:["oil","butter","cornflour","potato","carrots","onion","garlic","stock","salt","turmeric","pepper","chicken","pepper-red","peas"],
  ingredientLines:[
    {text:"2 tbsp oil + 1.5 tbsp butter"},
    {text:"3 tbsp cornstarch"},
    {text:"2 potatoes"},
    {text:"1 carrot + another small carrot, diced"},
    {text:"1 onion"},
    {text:"1 garlic clove"},
    {text:"500 ml chicken stock + 600 ml water"},
    {text:"1 tsp salt, 1/2 tsp turmeric, a pinch of pepper"},
    {text:"1 chicken breast (200-250 g)"},
    {text:"1/2 red bell pepper, diced"},
    {text:"50-80 g peas"},
    {text:"Topping: 1 tbsp butter + 1 tsp paprika"}
  ],
  steps:[
    "Heat the oil and butter in a pot.",
    "Add the cornstarch and toast briefly until golden.",
    "Roughly chop the potatoes, carrot, onion, and garlic, add them, and saute briefly.",
    "Add the stock, water, salt, turmeric, and pepper and stir.",
    "Place the whole chicken breast in the soup, cover, and simmer for 25 minutes.",
    "Remove the chicken and blend the soup until smooth and creamy.",
    "Shred the chicken with two forks and return it to the soup.",
    "Add the diced bell pepper, carrot, and peas and cook another 5-10 minutes until the vegetables are tender.",
    "For the topping: melt the butter with the paprika and drizzle over when serving."
  ],
  tips:"Blending the soup after removing the chicken is what makes it creamy — no cream at all."
},
{
  id:"71112", diet:"Vegetarian", image:"71112.jpg", category:"Salads",
  name:"Crunchy Green Holiday Salad",
  searchAlias:"סלט ירוקים קראנצ'י לחג",
  creator:"Elad Levi", time:"20 min", serves:"Serves 4-6",
  video:"https://www.facebook.com/reel/4381618362056491",
  intro:"A festive salad of firm, crunchy vegetables — cucumber, kohlrabi, and green apple — with loads of fresh herbs, a pomegranate-lemon dressing, and candied pecans.",
  needs:["cucumbers","kohlrabi","apple","celery","scallion","parsley","coriander","mint","olive-oil","lemon","pomegranate-molasses","salt","pepper","pecans"],
  ingredientLines:[
    {text:"Cucumbers — small dice"},
    {text:"Kohlrabi — small dice"},
    {text:"Green apple — small dice"},
    {text:"5-6 celery stalks, chopped"},
    {text:"Scallions, very finely chopped"},
    {text:"1 bunch parsley, 1 bunch cilantro, and 1 bunch mint — a must!"},
    {text:"Dressing: 1/2 cup olive oil"},
    {text:"Juice of a whole lemon"},
    {text:"2 tbsp pomegranate molasses"},
    {text:"1 tsp salt + 1/2 tsp coarsely ground black pepper"},
    {text:"On top: chopped candied pecans (or any nut) and pomegranate seeds"}
  ],
  steps:[
    "Cut the cucumber, kohlrabi, and green apple into small dice.",
    "Finely chop the celery, scallions, and herbs.",
    "Mix the dressing ingredients.",
    "Transfer the vegetables to a large bowl, add the dressing, and toss well.",
    "Plate and top with chopped candied pecans and pomegranate seeds."
  ],
  tips:"From the comments: the apple browns — the lemony dressing fixes that if you toss right away; no pomegranate molasses? Silan with extra lemon works."
}
);
