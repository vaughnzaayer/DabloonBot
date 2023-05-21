import discord
import json


class DabloonUser:
    def __init__(self, userid: discord.User.id):
        self.id = userid
        self.dabloonCount = 0

    def get_dabloons(self):
        return self.dabloonCount

    def add_dabloons(self, dabloons):
        self.dabloonCount += dabloons

    def subtract_dabloons(self, dabloons):
        self.dabloonCount -= dabloons

    def get_username(self):
        pass


class DabloonBounty:
    def __init__(self, title: str, author: DabloonUser, rewardAmount: int, claimAmount: str = 1,
                 totalClaimAmount: str = None, image: discord.Attachment = None,
                 description: str = None, url: str = None):
        self.title = title
        self.author = author
        self.reward = rewardAmount
        self.claimAmount = claimAmount
        self.totalClaimAmount = totalClaimAmount
        self.claimedBy = {}
        self.pendingClaims = {}
        self.image = image
        self.description = description
        self.url = url

    def user_claim(self, user):
        if user in self.claimedBy or self.claimedBy[user] == self.claimAmount:
            return

    def approve_claim(self, user):
        pass


class ClaimRequest:
    def __init__(self, bounty: DabloonBounty, claimee: DabloonUser):
        pass
