SELECT COUNT (DISTINCT U.userID)
FROM Users U, Items I
WHERE U.userID = I.userID AND U.rating > 1000;
