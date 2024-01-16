SELECT 
   distinct(t1.user_pseudo_id),
   t1.country,
   t1.app_language, 
   ifnull(COALESCE(t2.max_user_level, NULL),0) as max_user_level,
   ifnull(COALESCE(t2.gc, NULL), 0) as gc,
   ifnull(COALESCE(t2.max_game_level, NULL),0) as max_game_level,
   COALESCE(t2.la_date, NULL) as la_date,
   t1.first_open

FROM `dataexploration-193817.user_data.user_first_open_list` AS t1
LEFT JOIN `dataexploration-193817.user_data.users_data` AS t2
ON t1.user_pseudo_id = t2.user_pseudo_id