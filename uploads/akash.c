#include<stdio.h>
int main()
{
	int marks;
	printf("enter the marks of student:/n");
	scanf("%d",&marks);
	if((marks>=35)&&(marks<=100))
	{
		printf("this person is passed in final exam");
	}
	else
	{
		printf("this person is failed in final exam");
	}
	return 0;
}
