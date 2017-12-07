## Final project: meeting time maker 

Snarf appointment data from a selection of a user's Google calendars with busy/free time options available

- Orignal author: Michal Young
- Author: Xin(Adam) Chen
- Contact Email: achen@uoregon.edu
- Contact Address: University of Oregon, 1585 E 13th Ave, Eugene, OR 97403

## Functions (will come soon)

Application allows a creator to choose a date and time range for listing all free and busy events during that period

- it will ask user login in with customizable username and password
- user can choose calendars to display all calednars and select events in selected calendars, then 'submit'
- after displaying all busy events, users still can mark some events being ingored, then 'submit'
- Free and busy time will be shown in order

Creator can share a link to group members so that they can pick their own busy time

- group members can share their link to others too!

Finally creator can see free time during the date/time range by clicking ' check final free time' button

## Test

- nosetests is ready for testing but it only works for a specified calendar (my calendar actually)
- To test "Share Link", using two different browsers will be strongly recommended (currently it only works on localhost. I may try to deploy it on Cloud-server)
## Usage

```
git clone < repo link > < your directory >
cd < your directory >
make run
open your browser and go to localhost:5000
```

## Requirement

1. a credential file
2. one google calendar json file

## Known bugs
1. If the time range is from 00:00 to 00:00, there's no output. Please use 00:00 to 23:59
2. ugly layout of page !
3. If creator click "check final free" before he/she sumbit his/her busy time, it occrurs errors.
4. Since I use flask.session to store date/unique_id, users will lose them if they close their broswers (they cannot go back to check final free time)
   My idea is trying to use username to get data/unique_id again. Howver, no more time for me to revise them. Hence, I recommend grader opens one browser to create creator. Then enter "shared link" in another browser. After both of them submitted free/busy time, grader can test "checkfinalfree" button at first browser.
5. Wrong computation of free time. Still working with it.
