from django.db import models

class Product(models.Model):
    asin = models.CharField(max_length=10)
    geography = models.CharField(max_length=50, default='India')
    email = models.CharField(max_length=100, default='default@example.com')
    title = models.TextField()
    bullet_point_1 = models.TextField()
    bullet_point_2 = models.TextField()
    bullet_point_3 = models.TextField()
    bullet_point_4 = models.TextField()
    bullet_point_5 = models.TextField()
    description = models.TextField()

    def __str__(self):
        return self.asin
