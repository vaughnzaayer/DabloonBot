import discord
import json
import datetime


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


class ClaimRequest:
    def __init__(self, claimee: DabloonUser, description: str = None, media: [discord.Attachment] = None):
        self.claimee = claimee
        self.description = description
        self.media = media


class DabloonBounty:
    def __init__(self, title: str, author: DabloonUser, rewardAmount: int, claimAmount: str = 1,
                 totalClaimAmount: str = None, image: discord.Attachment = None,
                 description: str = None, url: str = None):
        self.title = title
        self.author = author
        self.reward = rewardAmount
        self.claimAmount = claimAmount
        self.totalClaimAmount = totalClaimAmount
        self.claimedBy: {DabloonUser: int} = {}
        self.pendingClaims: [ClaimRequest] = []
        self.image = image
        self.description = description
        self.url = url
        self.creationDate = datetime.date.today()

    def user_claim(self, request):
        self.pendingClaims.append(request)

    def approve_claim(self, request):
        request.claimee.add_dabloons(self.reward)
        self.claimedBy[request.claimee] += 1
        del request

    def reject_claim(self, request):
        del request

def write_to_json_database():
    pass

def read_from_json_database():
    pass


