# Sử dụng SDK 9.0 để build
FROM mcr.microsoft.com/dotnet/sdk:9.0 AS build
WORKDIR /src

# Copy các file dự án vào để restore
COPY ["AuraShop.API/AuraShop.API.csproj", "AuraShop.API/"]
COPY ["AuraShop.Core/AuraShop.Core.csproj", "AuraShop.Core/"]
COPY ["AuraShop.Data/AuraShop.Data.csproj", "AuraShop.Data/"]

RUN dotnet restore "AuraShop.API/AuraShop.API.csproj"

# Copy toàn bộ code và build
COPY . .
WORKDIR "/src/AuraShop.API"
RUN dotnet build "AuraShop.API.csproj" -c Release -o /app/build

FROM build AS publish
RUN dotnet publish "AuraShop.API.csproj" -c Release -o /app/publish /p:UseAppHost=false

# Runtime sử dụng ASP.NET 9.0
FROM mcr.microsoft.com/dotnet/aspnet:9.0
WORKDIR /app
COPY --from=publish /app/publish .
ENTRYPOINT ["dotnet", "AuraShop.API.dll"]