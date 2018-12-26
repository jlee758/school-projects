SELECT C.itemID
FROM (SELECT *
	FROM Items
	WHERE Currently = (SELECT Max(Currently)
	    FROM Items)) AS C;
