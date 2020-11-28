from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    pass

class Listing(models.Model):
    name = models.CharField(max_length=150, default="Item name")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="owner_id", null=True, blank=True)
    description = models.TextField(blank=True)
    startBid = models.IntegerField(default=0)
    imgSrc = models.URLField(blank=True)
    Q = 'Q'
    F = 'F'
    T = 'T'
    E = 'E'
    H = 'H'
    O = 'O'
    CATEGORY_CHOICES = [
        (Q, 'Quick sell'),
        (F, 'Fashion'),
        (T, 'Toys'),
        (E, 'Electronics'),
        (H, 'Home'),
        (O, 'Other')
    ]
    category = models.CharField(max_length=11, choices=CATEGORY_CHOICES)
    datePosted = models.DateTimeField(auto_now=True)
    isOpen = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.owner}'s {self.name} listed {self.datePosted}."

class Watchlist(models.Model):
    currentUser = models.ForeignKey(User, on_delete=models.CASCADE, related_name="current_user")
    itemWatch = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="watch_item")
    def __str__(self):
        return f"{self.currentUser} is watching: {self.itemWatch}"


class Bid(models.Model):
    listingID = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="listingBid", blank=True, null=True)
    bidder = models.ForeignKey(User, on_delete=models.CASCADE, related_name="whoBid", blank=True, null=True)
    amount = models.IntegerField(default=0)
    dateBid = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.bidder} bid ${self.amount} on {self.listingID}."

class Comment(models.Model):
    commenter = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user", blank=True, null=True)
    listingID = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="listingComment", blank=True, null=True)
    comment = models.CharField(max_length=264)
    dateCommented = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['dateCommented']

    def __str__(self):
        return f"{self.commenter} commented on {self.listingID}: '{self.comment}'"