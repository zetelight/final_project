# Under Construction. It will be ready for final project

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