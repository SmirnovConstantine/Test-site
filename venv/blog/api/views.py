from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import RetrieveAPIView
from rest_framework.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from main.models import Bd, Comments
from .serializers import BbSerializer, BbDetailSerializer, CommentSerializer


@api_view(['GET'])
def bbs(request):
    '''Сведения о 10 последних объявлениях.'''
    if request.method == 'GET':
        bbs = Bd.objects.filter(is_active=True)[:10]
        serializer = BbSerializer(bbs, many=True)
        return Response(serializer.data)



class BbDetailView(RetrieveAPIView):
    '''Сведения о конкретном объявлении.'''
    queryset = Bd.objects.filter(is_active=True)
    serializer_class = BbDetailSerializer




@api_view(['GET', 'PSOT'])
@permission_classes((IsAuthenticatedOrReadOnly,))
def comments(request, pk):
    if request.method == 'POST':
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
    else:
        comments = Comments.objects.filter(is_active=True, bb=pk)
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)
