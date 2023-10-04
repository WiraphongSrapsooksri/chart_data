# Use an appropriate base image
FROM ubuntu:20.04

RUN sed -i 's/archive.ubuntu.com/th.archive.ubuntu.com/g' /etc/apt/sources.list

# Update the package list and install required packages
RUN apt-get update && \
    apt-get install -y curl gnupg2 && \
    apt-get install -y python3 python3-pip && \
    apt-get install -y ca-certificates curl gnupg && \
    mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg && \
    rm -rf /var/lib/apt/lists/*

ENV NODE_MAJOR=20
RUN echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_$NODE_MAJOR.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list

RUN apt-get update && \
    apt-get install -y nodejs -y

WORKDIR /subj_api_app

# Copy Python requirements file first and install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy Node.js files and install Node.js dependencies
COPY package.json package-lock.json ./
RUN npm install -f

# Copy the rest of your application files
COPY . .

EXPOSE 3030

CMD ["node", "index.js", "-t", "86400"]