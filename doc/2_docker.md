# 1. Note For Isaac-ROS only
please follow this isaac-ros setup first: https://nvidia-isaac-ros.github.io/v/release-4.1/getting_started/index.html
 
# 2. Docker setup
```
cd ${MOVENSYS_PERCEPTION_PACKAGES}/docker                                                                              
docker compose -f ${MOVENSYS_ROS_VERSION}.yaml -f movensys_perception.${CPU_ARCH}.yaml down
docker compose -f ${MOVENSYS_ROS_VERSION}.yaml -f movensys_perception.${CPU_ARCH}.yaml build            
docker compose -f ${MOVENSYS_ROS_VERSION}.yaml -f movensys_perception.${CPU_ARCH}.yaml up -d 
```

# 3. Checkig Docker
```
docker logs movensys_perception_container -f
```

# 4. Running Docker
```
docker exec -it -u admin movensys_perception_container \
bash -lc 'source /opt/ros/${ROS_DISTRO}/setup.bash && \
        source /home/admin/ws/install/setup.bash && \
exec bash -i'
```