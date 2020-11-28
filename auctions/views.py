from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from django import forms, template
from django.forms import ModelForm
import django.contrib.messages
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from auctions.models import User, Listing, Bid, Comment, Watchlist

# Define iterables
CATEGORY_CHOICES = (
        ('Q', 'Quick sell'),
        ('F', 'Fashion'),
        ('T', 'Toys'),
        ('E', 'Electronics'),
        ('H', 'Home'),
        ('O', 'Other')
)
# Define form classes
class NewForm(forms.Form):
    name = forms.CharField(label='Item name', max_length=100, required=True)
    desc = forms.CharField(widget=forms.Textarea, label='Item description')
    startBid = forms.IntegerField(label='Price ($)', min_value=1, required=True)
    imgSrc = forms.URLField(label='Add an image URL', required=False)
    category = forms.ChoiceField(choices=CATEGORY_CHOICES, label='Category')

class BidForm(forms.Form):
    bid = forms.IntegerField(min_value=0)

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('comment',)

class CategoryForm(forms.Form):
    category = forms.ChoiceField(choices=CATEGORY_CHOICES, label='Choose a category')

# Define views
def index(request):
    # get all listings
    listings = Listing.objects.filter(isOpen = True).order_by('-id')
    return render(request, "auctions/index.html", {
        "listing": listings
        })

def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")

@login_required
def new(request):
    if request.method == 'POST':
        form = NewForm(request.POST)
        if form.is_valid():
            # get cleaned data from form
            name = form.cleaned_data['name']
            desc = form.cleaned_data['desc']
            startBid = form.cleaned_data['startBid']
            if form.cleaned_data['imgSrc']:
                imgSrc = form.cleaned_data['imgSrc']
            else:
                imgSrc = "#"
            if form.cleaned_data['category']:
                category = form.cleaned_data['category']
            # get user id and store in owner
            current_id = request.user.id
            owner = User.objects.get(id=current_id)
            # store cleaned data in listings table
            newlisting = Listing(name=name, description=desc, startBid=startBid, imgSrc=imgSrc, category=category, owner=owner)
            newlisting.save()
            
            message = django.contrib.messages.success(request, 'New listing added successfully.')
            return redirect("/", {
                "messages":message
            })
    else:
        form = NewForm()
    return render(request, "auctions/new.html", {"form":form})


def listing(request, listing_id):
    item = Listing.objects.get(id=listing_id)
    item_id = item.id
    user = request.user.username
    id_user = request.user
    bidform = BidForm()
    userWatchlist = Watchlist.objects.filter(currentUser=id_user)
    commentForm = CommentForm()
    numBids = len(Bid.objects.filter(listingID=listing_id))
    comments = Comment.objects.filter(listingID=listing_id)

    if request.method == 'POST':

        # Comment
        if 'commentButton' in request.POST:
            commentForm = CommentForm(data=request.POST)
            if commentForm.is_valid():
                # Create new comment object
                new_comment = Comment()
                new_comment = commentForm.save(commit=False)
                new_comment.listingID = item
                new_comment.commenter = id_user
                new_comment.save()
                message = django.contrib.messages.success(request, 'Comment added successfully.')
                return redirect("/", {"messages":message})
                
        # Watchlist
        if 'watchlistButton' in request.POST:
            # Check if item in userWatchlist
            for row in userWatchlist:
                if item == row.itemWatch:
                    # Remove item from watchlist if item in watchlist
                    userWatchlist.filter(itemWatch=item).delete()
                    message = django.contrib.messages.success(request, 'Item removed from watchlist.')
                    return redirect("/", {"messages":message})
            # Add item to watchlist
            w = Watchlist(currentUser=id_user, itemWatch=item)
            w.save()
            message = django.contrib.messages.success(request, 'Item added to watchlist.')
            return redirect("/", {"messages":message})
           
        # Place a bid      
        if 'makeBid' in request.POST:    
            bidform = BidForm(request.POST)
            if bidform.is_valid(): 
                user_bid = bidform.cleaned_data['bid']
                price = item.startBid

                # Validation: check user bid > item.startBid
                if user_bid > price:
                    # save bid to Bids
                    newBid = Bid(listingID=item, bidder=request.user, amount=user_bid)
                    newBid.save()
                    # save bid to item.startBid
                    item.startBid = user_bid
                    item.save()
                    message = django.contrib.messages.success(request, 'Bid placed successfully.')
                    return redirect("/", {"messages":message})
                else:
                    message = django.contrib.messages.success(request, 'Error: please bid an amount larger than the current price.')
                    return redirect("/", {"messages":message})
        
        # Close Auction Button if owner logged in
        elif 'closeAuction' in request.POST:
            item.isOpen = False
            # get winning bid
            topBid = item.startBid
            # get top Bid model
            topBidObject = Bid.objects.get(amount = topBid, listingID=item_id)
            # get top Bidder from top Bid model
            topBidder = topBidObject.bidder
            # set item owner to top bidder
            item.owner = topBidder
            item.save()
            message = django.contrib.messages.success(request, 'Closed auction successfully.')
            return redirect("/", {"messages":message})
   
    else:
        # get number of bids on items
        try:
            whoBid = Bid.objects.filter(bidder=request.user)[0]
            whoBid1 = whoBid.bidder
            numBids = len(Bid.objects.filter(listingID=listing_id))
            return render(request, "auctions/listing.html", {
                "item": item,
                "user_id": user,
                "commentForm": commentForm,
                "bidForm": bidform,
                "numBids": numBids,
                "whoBid": whoBid1,
                "watchlist": userWatchlist,
                "comments": comments
            })
        except:
            numBids = len(Bid.objects.filter(listingID=listing_id))
            return render(request, "auctions/listing.html", {
                "item": item,
                "user_id": user,
                "commentForm": commentForm,
                "bidForm": bidform,
                "numBids": numBids,
                "watchlist": userWatchlist,
                "comments": comments
            })

@login_required
def watchlist(request):
    id_user = request.user
    listings = Listing.objects.filter(isOpen = True).order_by('-id')
    user_watchlist = Watchlist.objects.filter(currentUser=id_user).order_by('-id')
    return render(request, "auctions/watchlist.html", {
        "watchlist": user_watchlist,
        "listing":listings,
    })


@login_required
def categories(request):
    if request.method == 'POST':
        # display all items with the posted data as their category
        category_form = CategoryForm(request.POST)
        if category_form.is_valid():
            category_chosen = category_form.cleaned_data['category']
            print(category_chosen)
            items = Listing.objects.filter(category=category_chosen)
            return render(request, "auctions/categories.html", {
            "category_form":category_form,
            "items":items
        })
    else:
        category_form = CategoryForm()
        return render(request, "auctions/categories.html", {
            "category_form":category_form
        })
