/* Cookin — batch 5 (2026-09-01): 3 dishes synced from the WhatsApp group */

Object.assign(INGREDIENTS, {
  figs:           {label:"Figs", group:"Vegetables & Fruit", subs:[]},
  breadcrumbs:    {label:"Breadcrumbs", group:"Pantry & Canned", subs:["flour"]},
  paprika:        {label:"Sweet paprika", group:"Pantry & Canned", subs:["spices"]},
  "curry-yellow": {label:"Yellow curry paste", group:"Asian Pantry", subs:["curry-red"]}
});

RECIPES.push(
{
  id:"71154", diet:"Meat", image:"71154.jpg", category:"Chicken",
  name:"Chicken with Figs and Red Onion",
  searchAlias:"עוף בתאנים ובצל סגול",
  creator:"Itay Edri", time:"1 hr 45 min", serves:"Serves 8",
  video:"https://www.facebook.com/reel/1071848778713858",
  intro:"A festive holiday dish: chicken drumsticks on a bed of red onion with figs that caramelize in the oven in a honey-thyme sauce. Minimum effort, maximum wow.",
  needs:["chicken","red-onion","figs","pepper","salt","honey-silan","olive-oil","water","thyme"],
  ingredientLines:[
    {text:"16 chicken drumsticks"},
    {text:"6 medium red onions"},
    {text:"20 figs"},
    {text:"1 teaspoon coarsely ground black pepper"},
    {text:"1½ teaspoons salt"},
    {text:"3 tablespoons honey"},
    {text:"¼ cup olive oil"},
    {text:"½ cup boiling water"},
    {text:"A few sprigs of thyme"}
  ],
  steps:[
    "Cut the red onions into strips and arrange them on the bottom of a baking dish. Sprinkle with a little black pepper and drizzle with a little olive oil.",
    "Arrange the chicken drumsticks on top, quarter the figs and scatter them between the chicken pieces. Lay the thyme sprigs on top.",
    "Make a sauce from the honey, olive oil, boiling water, black pepper, and salt — mix well and pour evenly over the chicken and figs.",
    "Cover with parchment paper topped with aluminum foil and bake in an oven preheated to 190°C for an hour and a half.",
    "Remove the cover and bake another 10-15 minutes on top convection until nicely browned. Serve hot — the sauce is sweet and rich with the caramelized onions and figs."
  ],
  tips:"From the comments: worth making for a holiday, but figs are pricey (35-45 ₪ per kilo) — you can cut the amount or swap some for plums. Also works with whole chicken thighs."
},
{
  id:"71156", diet:"Meat", image:"71156.jpg", category:"Beef",
  name:"Jumbo Meatballs in Lemon Sauce",
  searchAlias:"קציצות ג'מבו ברוטב לימון",
  creator:"Itay Edri", time:"2 hrs", serves:"Serves 6",
  video:"https://www.facebook.com/reel/1805302633965686",
  intro:"Big, fatty meatballs made from well-marbled ground beef, simmered in a lemony sauce with celery leaves and beet greens. The fat melts into the sauce and thickens it into a tangy, rich gravy. Served with rice.",
  needs:["beef","breadcrumbs","eggs","paprika","cream-cheese","salt","pepper","onion","parsley","celery","flour","beets","garlic","lemon","sugar","olive-oil"],
  ingredientLines:[
    {text:"Meatballs: 1.2 kg fatty ground beef (originally: goose-cut short ribs)"},
    {text:"1 cup breadcrumbs"},
    {text:"2 eggs"},
    {text:"1 tablespoon coarsely ground sweet paprika"},
    {text:"1 tablespoon cream cheese (Philadelphia)"},
    {text:"1½ teaspoons fine salt + 1 teaspoon coarsely ground black pepper"},
    {text:"2 grated onions"},
    {text:"1 bunch parsley, chopped"},
    {text:"Celery stalks, finely chopped"},
    {text:"Flour for dredging"},
    {text:"Sauce: celery leaves + beet greens"},
    {text:"1 chopped onion + 3 sliced garlic cloves"},
    {text:"1 lemon, peeled and sliced + juice of 2 lemons"},
    {text:"1 teaspoon salt, 2 teaspoons brown sugar, 1 teaspoon black pepper"},
    {text:"½ cup olive oil"}
  ],
  steps:[
    "Put all the meatball ingredients in a bowl and mix well. Form large meatballs and dredge them in flour.",
    "Fry them in a wide pot with the olive oil on all sides until browned.",
    "Add the chopped onion and sliced garlic to the pot, squeeze in the lemon juice and add the lemon slices. Cover with water up to the level of the meatballs.",
    "Add the salt, black pepper, brown sugar, celery leaves, and beet greens. Bring to a boil and simmer over low heat for about an hour and a quarter, until the meatballs are tender and the sauce has thickened (add a little water if needed).",
    "Serve hot with white rice."
  ],
  tips:"It's important to use meat with a high fat content — the fat melts into the sauce and thickens it. From the comments: if you don't like celery, you can swap in leek."
},
{
  id:"71279", diet:"Meat", image:"71279.jpg", category:"Chicken",
  name:"Easy Yellow Chicken Curry (Reconstructed)",
  searchAlias:"קארי עוף צהוב קליל (משוחזר)",
  creator:"foodinfivemins", time:"40 min", serves:"Serves 3",
  video:"https://www.facebook.com/reel/1025871130212335",
  intro:"A high-protein yellow chicken curry with green beans and carrots in coconut milk. 724 calories and 53 grams of protein per serving. Ingredients are from the original caption; the steps are reconstructed from the video.",
  needs:["chicken","spices","greek-yogurt","olive-oil","onion","garlic","chili","curry-yellow","green-beans","carrots","coconut-milk","stock","coriander","rice"],
  ingredientLines:[
    {text:"700 g boneless chicken thighs"},
    {text:"Marinade: 1 tablespoon curry powder, 1 teaspoon chili powder, 1 teaspoon onion powder, 1 teaspoon garlic powder"},
    {text:"2 tablespoons Greek yogurt + 2 tablespoons olive oil"},
    {text:"1 shallot (or half a regular onion)"},
    {text:"3 garlic cloves + 1 mild chili"},
    {text:"3 tablespoons yellow curry paste"},
    {text:"200 g green beans + 3 carrots"},
    {text:"300 ml coconut milk + 100 ml chicken stock"},
    {text:"To serve: 200 g rice, fresh chili, cilantro, crispy fried onions"}
  ],
  steps:[
    "Mix the chicken thighs with the curry, chili, onion, and garlic powders, the yogurt, and a tablespoon of olive oil. Marinate for 15 minutes (or longer).",
    "Sear the chicken in a hot pan until nicely browned on both sides and set aside.",
    "In the same pan, sauté the chopped shallot, sliced garlic, and chili in the remaining oil, about 2 minutes. Add the yellow curry paste and fry another minute until fragrant.",
    "Add the coconut milk and chicken stock and stir into a smooth sauce. Add the sliced carrots and green beans and cook for 8-10 minutes.",
    "Return the chicken to the sauce and cook another 5-8 minutes until the chicken is done and the sauce has thickened.",
    "Serve over rice with fresh chili, cilantro, and crispy fried onions."
  ],
  tips:"Reconstructed — the full written recipe was gated behind 'comment recipe'. Nutrition per serving: 53 g protein / 25 g fat / 72 g carbs / 724 calories."
}
);
