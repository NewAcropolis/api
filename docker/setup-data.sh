#!/bin/bash
set -o pipefail

GITHUB_SHA=$(git rev-parse HEAD) ./scripts/check_site.sh na_api:5001/info no_workers

# import venues
./integration_test.sh -iv
# import speakers
./integration_test.sh -is
# import event types
./integration_test.sh -iet
# import events
./integration_test.sh -ie
# import articles
./integration_test.sh -ia
# import marketing
./integration_test.sh -ima
# import members
./integration_test.sh -ime
# import emails
./integration_test.sh -iem

# Upload articles images
python app_start.py upload_file data/article_images/AlchemistsGold.jpg --target_filename=articles/AlchemistsGold.jpg
python app_start.py upload_file data/article_images/Modern_Myth.jpg --target_filename=articles/Modern_Myth.jpg
python app_start.py upload_file data/article_images/Play_Chess.jpg --target_filename=articles/Play_Chess.jpg
python app_start.py upload_file data/article_images/Beethoven.jpg --target_filename=articles/Beethoven.jpg
python app_start.py upload_file data/article_images/Victor_Schauberger.jpg --target_filename=articles/Victor_Schauberger.jpg

python app_start.py upload_file data/article_images/AlchemistsGold.jpg --target_filename=thumbnail/articles/AlchemistsGold.jpg
python app_start.py upload_file data/article_images/Modern_Myth.jpg --target_filename=thumbnail/articles/Modern_Myth.jpg
python app_start.py upload_file data/article_images/Play_Chess.jpg --target_filename=thumbnail/articles/Play_Chess.jpg
python app_start.py upload_file data/article_images/Beethoven.jpg --target_filename=thumbnail/articles/Beethoven.jpg
python app_start.py upload_file data/article_images/Victor_Schauberger.jpg --target_filename=thumbnail/articles/Victor_Schauberger.jpg

# Upload events images
python app_start.py upload_file data/event_images/Mind.jpg --target_filename=standard/2023/Mind.jpg
python app_start.py upload_file data/event_images/IntroCourse.jpg --target_filename=standard/2023/IntroCourse.jpg

python app_start.py upload_file data/event_images/Mind.jpg --target_filename=thumbnail/2023/Mind.jpg
python app_start.py upload_file data/event_images/IntroCourse.jpg --target_filename=thumbnail/2023/IntroCourse.jpg

# import magazines
python app_start.py upload_magazines
