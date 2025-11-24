import factory
from django.utils.text import slugify
from blog.models import Post

class PostFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Post

    title = factory.Faker("sentence", nb_words=4)
    slug = factory.LazyAttribute(lambda o: slugify(o.title))
    summary = factory.Faker("paragraph", nb_sentences=3)
    body_markdown = factory.Faker("text", max_nb_chars=2000)
    status = Post.Status.PUBLISHED
