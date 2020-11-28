from django.contrib import admin
from auctions.models import Listing, Bid, Comment, User, Watchlist

# Register your models here.
admin.site.register(User)
admin.site.register(Listing)
admin.site.register(Watchlist)
admin.site.register(Bid)

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('commenter', 'comment', 'listingID', 'dateCommented')
    list_filter = ('commenter', 'dateCommented')
    search_fields = ('commenter', 'comment')