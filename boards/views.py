from django.shortcuts import render,get_object_or_404,redirect

from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db.models import Count
from django.views.generic import UpdateView,ListView
from django.utils import timezone
from django.urls import reverse_lazy
from django.core.paginator import Paginator,EmptyPage,PageNotAnInteger
from django.contrib.auth.models import User
from .models import Board,Topic,Post
from .forms import NewTopicForm,PostForm

# Create your views here.

# def home(request):
#     boards=Board.objects.all()
#     context={'boards':boards}
#     return render(request,'home.html',context)
@method_decorator(login_required,name='dispatch')
class BoardListView(ListView):
    model = Board
    context_object_name = 'boards'
    template_name = 'home.html'

# @login_required
# def board_topics(request,pk):
#     board=get_object_or_404(Board,pk=pk)
#     queryset=board.topics.order_by('-last_updated').annotate(replies=Count('posts')-1)
#     page=request.GET.get('page',1)
#
#     paginator=Paginator(queryset,20)
#
#     try:
#         topics=paginator.page(page)
#     except PageNotAnInteger:
#         topics=paginator.page(1)
#     except EmptyPage:
#         topics=paginator.page(paginator.num_pages)
#
#     context={'board':board,'topics':topics}
#     return render(request,'topics.html',context)

@method_decorator(login_required,name='dispatch')
class TopicListView(ListView):
    model = Topic
    context_object_name = 'topics'
    template_name = 'topics.html'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        kwargs['board']=self.board
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        self.board=get_object_or_404(Board,pk=self.kwargs.get('pk'))
        queryset=self.board.topics.order_by('-last_updated').annotate(replies=Count('posts')-1)
        return queryset

@login_required
def new_topic(request,pk):
    board=get_object_or_404(Board,pk=pk)

    if request.method=='POST':
        form=NewTopicForm(request.POST)
        if form.is_valid():
            topic=form.save(commit=False)  #commit=False代表不要提交到数据库中
            topic.board=board
            topic.starter=request.user
            topic.save()  #这次保存到数据库中
            post=Post.objects.create(
                message=form.cleaned_data.get('message'),  #获取表单中对应message中的数据
                topic=topic,
                created_by=request.user
            )
            #redirect函数重定向到某一url
            return redirect('topic_posts',pk=pk,topic_pk=topic.pk)
    else:
            form=NewTopicForm()  #创建空表单
    context={'board':board,'form':form}
    return render(request,'new_topic.html',context)

# def topic_posts(request,pk,topic_pk):
#     topic=get_object_or_404(Topic,board__pk=pk,pk=topic_pk)
#     topic.views+=1
#     topic.save()
#     context={'topic':topic}
#     return render(request,'topic_post.html',context)

@method_decorator(login_required,name='dispatch')
class PostListView(ListView):
    model = Post
    context_object_name = 'posts'
    template_name = 'topic_post.html'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        session_key='viewed_topic_{}'.format(self.topic.pk)
        if not self.request.session.get(session_key, False):
            self.topic.views+=1
            self.topic.save()
            self.request.session[session_key]=True

        kwargs['topic']=self.topic
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        self.topic=get_object_or_404(Topic,
            board__pk=self.kwargs.get('pk'),pk=self.kwargs.get('topic_pk'))
        queryset=self.topic.posts.order_by('-created_at')
        return queryset



@login_required
def reply_topic(request,pk,topic_pk):
    topic=get_object_or_404(Topic,board__pk=pk,pk=topic_pk)

    if request.method=='POST':
        form=PostForm(request.POST)
        if form.is_valid():
            post=form.save(commit=False)
            post.topic=topic
            post.created_by=request.user
            post.save()

            topic.last_updated=timezone.now()
            topic.save()

            return redirect('topic_posts',pk=pk,topic_pk=topic_pk)
    else:
        form=PostForm()

    context={'topic':topic,'form':form}
    return render(request,'reply_topic.html',context)

@method_decorator(login_required,name='dispatch')
class PostUpdateView(UpdateView):
    model = Post  #表单模型
    fields = ('message',)
    template_name = 'edit_post.html'
    pk_url_kwarg = 'post_pk'  #来标识⽤于检索 Post 对象的关键字参数的名称
    context_object_name = 'post'

    def get_queryset(self):
        queryset=super().get_queryset()  #重用父类
        return queryset.filter(created_by=self.request.user)

    def form_valid(self, form):  #重写form_valid方法
        post=form.save(commit=False)
        post.updated_by=self.request.user
        post.updated_at=timezone.now()
        post.save()
        return redirect('topic_posts',pk=post.topic.board.pk,topic_pk=post.topic.pk)

class UserUpdateView(UpdateView):
    model = User
    fields = ('first_name','last_name','email',)
    template_name = 'my_account.html'
    success_url = reverse_lazy('my_account')

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        return redirect('home')

