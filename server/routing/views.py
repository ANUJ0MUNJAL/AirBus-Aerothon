from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework import status 

from .models import *
from django.contrib.auth.models import User

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from rest_framework_simplejwt.authentication import JWTAuthentication 
from rest_framework_simplejwt.tokens import Token

from rest_framework.views import APIView
from rest_framework.response import Response
from userLogin.serializers import *
from django.http import HttpResponse

import numpy as np
import matplotlib.pyplot as plt
import heapq

class Node:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.parent = None
        self.cost = float('inf')  # Set initial cost to infinity

    def __lt__(self, other):
        return self.cost < other.cost

def distance(node1, node2):
    return np.sqrt((node1.x - node2.x)**2 + (node1.y - node2.y)**2)

def is_collision_free(node, obstacle_list, obstacle_radius):
    for (ox, oy) in obstacle_list:
        if distance(node, Node(ox, oy)) <= obstacle_radius:
            return False
    return True

def get_path(goal_node):
    path = [(goal_node.x, goal_node.y)]
    node = goal_node
    while node.parent is not None:
        node = node.parent
        path.append((node.x, node.y))
    return path[::-1]

def dijkstra(start, goal, obstacle_list, obstacle_radius, search_area):
    start_node = Node(start[0], start[1])
    goal_node = Node(goal[0], goal[1])
    start_node.cost = 0

    open_set = []
    heapq.heappush(open_set, start_node)
    visited = set()
    node_list = [start_node]

    while open_set:
        current_node = heapq.heappop(open_set)
        
        if (current_node.x, current_node.y) in visited:
            continue

        if distance(current_node, goal_node) <= 1.0:  # Goal is reached
            goal_node.parent = current_node
            goal_node.cost = current_node.cost + distance(current_node, goal_node)
            node_list.append(goal_node)
            break

        visited.add((current_node.x, current_node.y))

        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                
                new_x = current_node.x + dx
                new_y = current_node.y + dy

                if not (search_area[0] <= new_x <= search_area[1] and search_area[2] <= new_y <= search_area[3]):
                    continue
                
                new_node = Node(new_x, new_y)

                if is_collision_free(new_node, obstacle_list, obstacle_radius) and (new_node.x, new_node.y) not in visited:
                    new_cost = current_node.cost + distance(current_node, new_node)

                    if new_cost < new_node.cost:
                        new_node.cost = new_cost
                        new_node.parent = current_node
                        heapq.heappush(open_set, new_node)
                        node_list.append(new_node)

    path = get_path(goal_node)
    return path, node_list

def draw_graph(node_list, path, start, goal, obstacle_list, obstacle_radius, search_area):
    plt.figure(figsize=(10, 10))
    plt.plot(start[0], start[1], "go")
    plt.plot(goal[0], goal[1], "ro")
    for node in node_list:
        if node.parent:
            plt.plot([node.x, node.parent.x], [node.y, node.parent.y], "-g")
    for (ox, oy) in obstacle_list:
        circle = plt.Circle((ox, oy), obstacle_radius, color='r')
        plt.gca().add_patch(circle)
    if path:
        plt.plot([x for (x, y) in path], [y for (x, y) in path], '-r')
    plt.xlim(search_area[0], search_area[1])
    plt.ylim(search_area[2], search_area[3])
    plt.grid(True)
    plt.show()

class RouteFinding(APIView):
    authentication_classes = [JWTAuthentication]
    def get(self, request):
        if "start" in request.data and "goal" in request.data:
            start = request.data["start"]
            goal = request.data["goal"]

            obstacle_list = []
            if "obstacle_list" in request.data:
                obstacle_list = request.data["obstacle_list"]
            obstacle_radius = 0
            if "obstacle_radius" in request.data:
                obstacle_radius = request.data["obstacle_radius"]

            search_area = Node.objects.all().values_list('x', 'y')

            if not search_area:
                search_area = [(0, 100), (0, 100)]  # default search area if not specified

            path, node_list = dijkstra(start, goal, obstacle_list, obstacle_radius, search_area)
            return Response({"path": path, "node_list": [(node.x, node.y) for node in node_list]})
        
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)
