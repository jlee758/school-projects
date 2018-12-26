SELECT COUNT (DISTINCT Users.userID)
FROM Items, Users, Bids
WHERE Items.userID = Users.userID AND Bids.userID = Items.userID;
