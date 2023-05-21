# Dabloon Bank Bot

## *Features*

### Users
- Users can be added or removed to the user database
- Each user has their total dabloon amount saved by the bot
- Total user amounts can be displayed by any person (using the dabloon emojis)

### Bounties
- Any user can create any number of bounties at any time
- Bounty parameters are the following:
  - title
  - description
  - author
  - number of times the bounty can be claimed *per user* (defaults to 1)
  - number of times the bounty can be claimed *total* (defaults to no limit)
  - **(optional)** image attachment
  - **(optional)** expiration date
  - **(optional)** whether or not the submission will be placed in an associated media channel
- Each bounty will track the following:
  - users that have claimed the bounty (approved claims)
  - how many times a user has claimed a bounty (if applicable)
  - media associated with the bounty
    - will be reposted in a separate channel w/ credit any bounty info
  - claim requests (author of the bounty cannot claim their own)
- The process of claiming a bounty will be the following:
1. a user will use `claim_bounty` with a claim or media related to the submission
2. a claim request (containing all related info and media) will be sent via DM to the author to approve/disapprove
   1. if a claim is accepted, the bounty reward will be given to the claimee and the media will be posted to the relevant channel
   2. if a claim is denied, the claimee will be notified via DM and the request will be deleted
