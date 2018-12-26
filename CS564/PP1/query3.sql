SELECT COUNT (*)
FROM (SELECT COUNT (Categories.itemID) AS numCat
  FROM Items
  LEFT JOIN Categories
  ON (Items.itemID = Categories.itemID)
  GROUP BY Items.itemID) AS C
WHERE C.numCat = 4;
