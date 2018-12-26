SELECT COUNT (DISTINCT C.category)
FROM Categories C, Bids B
WHERE C.itemID = B.itemID AND B.amount > 100;
