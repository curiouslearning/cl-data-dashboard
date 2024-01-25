SELECT
    a.user_pseudo_id,
    a.first_open,
    a.country,
    c.la_date as la_date,
    a.app_language,
    MAX(a.level) as max_user_level,
    SAFE_DIVIDE(MAX(a.level), b.max_level) * 100 as gpc,
    b.max_level as max_game_level
FROM
    `dataexploration-193817.user_data.all_users` a
LEFT JOIN
    (
        SELECT
            user_pseudo_id,
            MIN(event_date) as la_date
        FROM
            `dataexploration-193817.user_data.all_users`

        GROUP BY
            user_pseudo_id
    ) c
ON
    c.user_pseudo_id = a.user_pseudo_id
LEFT JOIN
    (
        SELECT
            app_language,
            max_level
        FROM
            `dataexploration-193817.user_data.language_max_level`
        GROUP BY
            app_language, max_level
    ) b
ON
    b.app_language = a.app_language
GROUP BY
    a.user_pseudo_id, a.first_open, a.country, c.la_date, a.app_language, b.max_level

